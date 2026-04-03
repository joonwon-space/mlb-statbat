"""Ingest MLB pitching stats into PostgreSQL.

Usage:
    python ingest_pitching.py --season 2025
    python ingest_pitching.py --season 2025 --qual 30
"""

import argparse
import logging
import os

import pandas as pd
from dotenv import load_dotenv
from pybaseball import pitching_stats
from sqlalchemy import create_engine, text

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://statbat:changeme@localhost:5432/statbat",
).replace("asyncpg", "psycopg2")


def fetch_pitching(season: int, qual: int = 30) -> pd.DataFrame:
    """Fetch season pitching stats via pybaseball."""
    logger.info("Fetching %d pitching stats from FanGraphs (qual=%d)...", season, qual)
    df = pitching_stats(season, qual=qual)
    logger.info("Retrieved %d pitcher rows", len(df))
    return df


COLUMN_MAP = {
    "IDfg": "player_mlb_id",
    "Season": "season",
    "Team": "team",
    "G": "games",
    "GS": "games_started",
    "IP": "innings_pitched",
    "W": "wins",
    "L": "losses",
    "SV": "saves",
    "SO": "strikeouts",
    "BB": "walks",
    "HR": "home_runs_allowed",
    "ERA": "era",
    "WHIP": "whip",
    "FIP": "fip",
    "xFIP": "xfip",
    "K/9": "k_per_9",
    "BB/9": "bb_per_9",
    "HR/9": "hr_per_9",
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
    name_parts = players["name_display"].str.split(" ", n=1, expand=True)
    players = players.copy()
    players["name_first"] = name_parts[0]
    players["name_last"] = name_parts[1].fillna("")
    players = players.drop_duplicates(subset=["mlb_id"])

    # Pitching stats
    available = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    stats = df[list(available.keys())].rename(columns=available)
    if "season" not in stats.columns:
        stats = stats.copy()
        stats["season"] = season

    return players, stats


def load(players: pd.DataFrame, stats: pd.DataFrame) -> None:
    """Insert data into PostgreSQL, upserting on conflict."""
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        # Upsert players
        for _, row in players.iterrows():
            conn.execute(
                text("""
                    INSERT INTO players (mlb_id, name_first, name_last, name_display, team)
                    VALUES (:mlb_id, :name_first, :name_last, :name_display, :team)
                    ON CONFLICT (mlb_id) DO UPDATE SET
                        team = EXCLUDED.team,
                        name_display = EXCLUDED.name_display
                """),
                dict(row),
            )

        # Upsert pitching stats
        for _, row in stats.iterrows():
            cols = [c for c in row.index if pd.notna(row[c])]
            values = {c: row[c] for c in cols}
            placeholders = ", ".join(f":{c}" for c in cols)
            col_names = ", ".join(cols)
            update_clause = ", ".join(
                f"{c} = EXCLUDED.{c}" for c in cols if c not in ("player_mlb_id", "season")
            )
            conn.execute(
                text(f"""
                    INSERT INTO pitching_stats ({col_names})
                    VALUES ({placeholders})
                    ON CONFLICT (player_mlb_id, season) DO UPDATE SET
                        {update_clause}
                """),
                values,
            )

    logger.info("Loaded %d players, %d pitching stat rows", len(players), len(stats))


def main():
    parser = argparse.ArgumentParser(description="Ingest MLB pitching stats")
    parser.add_argument("--season", type=int, default=2025, help="Season year")
    parser.add_argument(
        "--qual",
        type=int,
        default=30,
        help="Minimum innings pitched qualifier (default: 30)",
    )
    args = parser.parse_args()

    df = fetch_pitching(args.season, qual=args.qual)
    players, stats = transform(df, args.season)
    load(players, stats)
    logger.info("Done!")


if __name__ == "__main__":
    main()
