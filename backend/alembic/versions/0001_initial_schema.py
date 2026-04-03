"""Initial schema: players, batting_stats, pitching_stats.

Revision ID: 0001
Revises:
Create Date: 2026-04-03
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- players ---
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mlb_id", sa.Integer(), nullable=False),
        sa.Column("name_first", sa.String(100), nullable=False),
        sa.Column("name_last", sa.String(100), nullable=False),
        sa.Column("name_display", sa.String(200), nullable=False),
        sa.Column("position", sa.String(10), nullable=True),
        sa.Column("team", sa.String(50), nullable=True),
        sa.Column("bats", sa.String(1), nullable=True),
        sa.Column("throws", sa.String(1), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mlb_id"),
    )
    op.create_index("ix_players_mlb_id", "players", ["mlb_id"], unique=True)

    # --- batting_stats ---
    op.create_table(
        "batting_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("player_mlb_id", sa.Integer(), nullable=False),
        sa.Column("season", sa.SmallInteger(), nullable=False),
        sa.Column("team", sa.String(50), nullable=True),
        sa.Column("games", sa.Integer(), nullable=True),
        sa.Column("plate_appearances", sa.Integer(), nullable=True),
        sa.Column("at_bats", sa.Integer(), nullable=True),
        sa.Column("hits", sa.Integer(), nullable=True),
        sa.Column("doubles", sa.Integer(), nullable=True),
        sa.Column("triples", sa.Integer(), nullable=True),
        sa.Column("home_runs", sa.Integer(), nullable=True),
        sa.Column("rbi", sa.Integer(), nullable=True),
        sa.Column("runs", sa.Integer(), nullable=True),
        sa.Column("stolen_bases", sa.Integer(), nullable=True),
        sa.Column("walks", sa.Integer(), nullable=True),
        sa.Column("strikeouts", sa.Integer(), nullable=True),
        sa.Column("batting_avg", sa.Float(), nullable=True),
        sa.Column("obp", sa.Float(), nullable=True),
        sa.Column("slg", sa.Float(), nullable=True),
        sa.Column("ops", sa.Float(), nullable=True),
        sa.Column("wrc_plus", sa.Integer(), nullable=True),
        sa.Column("war", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "player_mlb_id", "season", name="uq_batting_player_season"
        ),
    )
    op.create_index(
        "ix_batting_stats_player_mlb_id", "batting_stats", ["player_mlb_id"]
    )
    op.create_index("ix_batting_stats_season", "batting_stats", ["season"])

    # --- pitching_stats ---
    op.create_table(
        "pitching_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("player_mlb_id", sa.Integer(), nullable=False),
        sa.Column("season", sa.SmallInteger(), nullable=False),
        sa.Column("team", sa.String(50), nullable=True),
        sa.Column("games", sa.Integer(), nullable=True),
        sa.Column("games_started", sa.Integer(), nullable=True),
        sa.Column("innings_pitched", sa.Float(), nullable=True),
        sa.Column("wins", sa.Integer(), nullable=True),
        sa.Column("losses", sa.Integer(), nullable=True),
        sa.Column("saves", sa.Integer(), nullable=True),
        sa.Column("strikeouts", sa.Integer(), nullable=True),
        sa.Column("walks", sa.Integer(), nullable=True),
        sa.Column("home_runs_allowed", sa.Integer(), nullable=True),
        sa.Column("era", sa.Float(), nullable=True),
        sa.Column("whip", sa.Float(), nullable=True),
        sa.Column("fip", sa.Float(), nullable=True),
        sa.Column("k_per_9", sa.Float(), nullable=True),
        sa.Column("bb_per_9", sa.Float(), nullable=True),
        sa.Column("hr_per_9", sa.Float(), nullable=True),
        sa.Column("xfip", sa.Float(), nullable=True),
        sa.Column("war", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "player_mlb_id", "season", name="uq_pitching_player_season"
        ),
    )
    op.create_index(
        "ix_pitching_stats_player_mlb_id", "pitching_stats", ["player_mlb_id"]
    )
    op.create_index("ix_pitching_stats_season", "pitching_stats", ["season"])


def downgrade() -> None:
    op.drop_table("pitching_stats")
    op.drop_table("batting_stats")
    op.drop_table("players")
