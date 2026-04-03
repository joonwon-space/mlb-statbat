"""Ingest MLB batting stats into PostgreSQL.

Usage:
    python ingest_batting.py --season 2025
"""

import argparse
import logging
import os

import pandas as pd
from dotenv import load_dotenv
from pybaseball import batting_stats
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://statbat:changeme@localhost:5432/statbat",
).replace("asyncpg", "psycopg2")


def fetch_batting(season: int, qual: int = 50) -> pd.DataFrame:
    """Fetch season batting stats via pybaseball."""
    logger.info("Fetching %d batting stats from FanGraphs (qual=%d)...", season, qual)
    df = batting_stats(season, qual=qual)
    logger.info("  Retrieved %d player rows", len(df))
    return df


COLUMN_MAP = {
    "IDfg": "player_mlb_id",
    "Season": "season",
    "Team": "team",
    "G": "games",
    "PA": "plate_appearances",
    "AB": "at_bats",
    "H": "hits",
    "2B": "doubles",
    "3B": "triples",
    "HR": "home_runs",
    "RBI": "rbi",
    "R": "runs",
    "SB": "stolen_bases",
    "BB": "walks",
    "SO": "strikeouts",
    "AVG": "batting_avg",
    "OBP": "obp",
    "SLG": "slg",
    "OPS": "ops",
    "wRC+": "wrc_plus",
    "WAR": "war",
}

PLAYER_COLUMN_MAP = {
    "IDfg": "mlb_id",
    "Name": "name_display",
    "Team": "team",
}


def transform(df: pd.DataFrame, season: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Transform raw pybaseball output into DB-ready DataFrames."""
    # Players
    players = df[list(PLAYER_COLUMN_MAP.keys())].rename(columns=PLAYER_COLUMN_MAP)
    # Split name into first/last
    name_parts = players["name_display"].str.split(" ", n=1, expand=True)
    players["name_first"] = name_parts[0]
    players["name_last"] = name_parts[1].fillna("")
    players = players.drop_duplicates(subset=["mlb_id"])

    # Batting stats
    available = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    stats = df[list(available.keys())].rename(columns=available)
    if "season" not in stats.columns:
        stats["season"] = season

    return players, stats


def load(players: pd.DataFrame, stats: pd.DataFrame) -> None:
    """Insert data into PostgreSQL, upserting on conflict.

    Uses bulk executemany instead of row-by-row iteration for performance.
    Matches the pattern used in ingest_pitching.py.
    """
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        # Bulk upsert players
        player_records = players.where(players.notna(), None).to_dict("records")
        if player_records:
            conn.execute(
                text("""
                    INSERT INTO players (mlb_id, name_first, name_last, name_display, team)
                    VALUES (:mlb_id, :name_first, :name_last, :name_display, :team)
                    ON CONFLICT (mlb_id) DO UPDATE SET
                        team = EXCLUDED.team,
                        name_display = EXCLUDED.name_display
                """),
                player_records,
            )

        # Bulk upsert batting stats — build query from actual columns in the DataFrame
        stat_cols = list(stats.columns)
        update_cols = [c for c in stat_cols if c not in ("player_mlb_id", "season")]
        col_names = ", ".join(stat_cols)
        placeholders = ", ".join(f":{c}" for c in stat_cols)
        update_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)

        stat_records = stats.where(stats.notna(), None).to_dict("records")
        if stat_records:
            conn.execute(
                text(f"""
                    INSERT INTO batting_stats ({col_names})
                    VALUES ({placeholders})
                    ON CONFLICT (player_mlb_id, season) DO UPDATE SET
                        {update_clause}
                """),
                stat_records,
            )

    logger.info("Loaded %d players, %d batting stat rows", len(players), len(stats))


def main():
    parser = argparse.ArgumentParser(description="Ingest MLB batting stats")
    parser.add_argument("--season", type=int, default=2025, help="Season year")
    parser.add_argument(
        "--qual",
        type=int,
        default=50,
        help="Minimum plate appearances qualifier (default: 50)",
    )
    args = parser.parse_args()

    df = fetch_batting(args.season, qual=args.qual)
    players, stats = transform(df, args.season)
    load(players, stats)
    logger.info("Done!")


if __name__ == "__main__":
    main()
