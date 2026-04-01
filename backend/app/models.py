from sqlalchemy import Integer, String, Float, SmallInteger, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mlb_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name_first: Mapped[str] = mapped_column(String(100))
    name_last: Mapped[str] = mapped_column(String(100))
    name_display: Mapped[str] = mapped_column(String(200))
    position: Mapped[str | None] = mapped_column(String(10), nullable=True)
    team: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bats: Mapped[str | None] = mapped_column(String(1), nullable=True)
    throws: Mapped[str | None] = mapped_column(String(1), nullable=True)


class BattingStats(Base):
    __tablename__ = "batting_stats"
    __table_args__ = (
        UniqueConstraint("player_mlb_id", "season", name="uq_batting_player_season"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_mlb_id: Mapped[int] = mapped_column(Integer, index=True)
    season: Mapped[int] = mapped_column(SmallInteger)
    team: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Counting stats
    games: Mapped[int | None] = mapped_column(Integer, nullable=True)
    plate_appearances: Mapped[int | None] = mapped_column(Integer, nullable=True)
    at_bats: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doubles: Mapped[int | None] = mapped_column(Integer, nullable=True)
    triples: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_runs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rbi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    runs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stolen_bases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    walks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    strikeouts: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Rate stats
    batting_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    obp: Mapped[float | None] = mapped_column(Float, nullable=True)
    slg: Mapped[float | None] = mapped_column(Float, nullable=True)
    ops: Mapped[float | None] = mapped_column(Float, nullable=True)
    wrc_plus: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Advanced
    war: Mapped[float | None] = mapped_column(Float, nullable=True)
