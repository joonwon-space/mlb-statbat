# MLB StatBat — Architecture Overview

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python), SQLAlchemy async, PostgreSQL |
| Frontend | Next.js (TypeScript), Tailwind CSS, shadcn/ui |
| Data Pipeline | pybaseball (FanGraphs), pandas, psycopg2 |
| LLM | Anthropic Claude / OpenAI (text-to-SQL, stub — not yet wired) |
| Infrastructure | Docker Compose, Cloudflare Tunnel |

## DB Models

### `players` table (`backend/app/models.py` — `Player`)

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer | Primary key, autoincrement |
| `mlb_id` | Integer | Unique, indexed |
| `name_first` | String(100) | |
| `name_last` | String(100) | |
| `name_display` | String(200) | Full display name |
| `position` | String(10) | Nullable |
| `team` | String(50) | Nullable |
| `bats` | String(1) | Nullable |
| `throws` | String(1) | Nullable |

### `batting_stats` table (`backend/app/models.py` — `BattingStats`)

Unique constraint: `(player_mlb_id, season)`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer | Primary key, autoincrement |
| `player_mlb_id` | Integer | Indexed; references `players.mlb_id` |
| `season` | SmallInteger | |
| `team` | String(50) | Nullable |
| `games` | Integer | Nullable |
| `plate_appearances` | Integer | Nullable |
| `at_bats` | Integer | Nullable |
| `hits` | Integer | Nullable |
| `doubles` | Integer | Nullable |
| `triples` | Integer | Nullable |
| `home_runs` | Integer | Nullable |
| `rbi` | Integer | Nullable |
| `runs` | Integer | Nullable |
| `stolen_bases` | Integer | Nullable |
| `walks` | Integer | Nullable |
| `strikeouts` | Integer | Nullable |
| `batting_avg` | Float | Nullable |
| `obp` | Float | Nullable |
| `slg` | Float | Nullable |
| `ops` | Float | Nullable |
| `wrc_plus` | Integer | Nullable |
| `war` | Float | Nullable |

### `pitching_stats` table (`backend/app/models.py` — `PitchingStats`)

Unique constraint: `(player_mlb_id, season)`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer | Primary key, autoincrement |
| `player_mlb_id` | Integer | Indexed; references `players.mlb_id` |
| `season` | SmallInteger | |
| `team` | String(50) | Nullable |
| `games` | Integer | Nullable |
| `games_started` | Integer | Nullable |
| `innings_pitched` | Float | Nullable |
| `wins` | Integer | Nullable |
| `losses` | Integer | Nullable |
| `saves` | Integer | Nullable |
| `strikeouts` | Integer | Nullable |
| `walks` | Integer | Nullable |
| `home_runs_allowed` | Integer | Nullable |
| `era` | Float | Nullable |
| `whip` | Float | Nullable |
| `fip` | Float | Nullable |
| `k_per_9` | Float | Nullable |
| `bb_per_9` | Float | Nullable |
| `hr_per_9` | Float | Nullable |
| `xfip` | Float | Nullable |
| `war` | Float | Nullable |

## API Endpoints

| Method | Path | Handler |
|--------|------|---------|
| GET | `/health` | `health` |
| POST | `/api/query` | `query` |

Full request/response details: see [api-reference.md](./api-reference.md).

## LLM Pipeline (`backend/app/text_to_sql.py`)

**Status: stub — LLM calls not yet active.**

Three functions handle the query pipeline:

1. `generate_sql(question: str) -> str` — intended to call an LLM (Anthropic Claude or OpenAI) with `SYSTEM_PROMPT` containing the DB schema, and return a SELECT query. Currently raises `NotImplementedError`.
2. `_validate_select_only(sql: str) -> None` — SQL guard (using `sqlparse`) that enforces exactly one SELECT statement. Blocks DML/DDL, multi-statement injection via semicolons, and `SELECT INTO`. Raises `ValueError` on any violation, which the endpoint surfaces as HTTP 400.
3. `execute_sql(db: AsyncSession, sql: str) -> list[dict]` — calls `_validate_select_only`, then executes the SQL against PostgreSQL via SQLAlchemy async and returns rows as a list of dicts. DB errors are logged internally; the caller receives a generic HTTP 500.
4. `generate_answer(question, sql, rows) -> str` — intended to call an LLM to produce a human-friendly summary of the results. Currently returns a raw string representation.

The `SYSTEM_PROMPT` embeds the full DB schema (players, batting_stats, pitching_stats) so the LLM can generate accurate SQL without needing additional context at query time.

When the LLM is not configured, `POST /api/query` returns HTTP 501.

## Data Pipeline

Two scripts fetch stats from FanGraphs via the `pybaseball` library and upsert them into PostgreSQL.

### `data_pipeline/ingest_batting.py`

**CLI usage:**
```bash
python ingest_batting.py --season 2025
python ingest_batting.py --season 2025 --qual 100
```

**What it does:**
1. Calls `pybaseball.batting_stats(season, qual=50)` — returns all qualified batters for the season.
2. Transforms the raw FanGraphs DataFrame into `players` and `batting_stats` shapes.
3. Upserts into PostgreSQL (row-by-row):
   - `players` — on conflict by `mlb_id`, updates `team` and `name_display`.
   - `batting_stats` — on conflict by `(player_mlb_id, season)`, updates all stat columns.

**Qualification threshold:** `qual=50` (minimum plate appearances; configurable via `--qual`).

### `data_pipeline/ingest_pitching.py`

**CLI usage:**
```bash
python ingest_pitching.py --season 2025
python ingest_pitching.py --season 2025 --qual 50
```

**What it does:**
1. Calls `pybaseball.pitching_stats(season, qual=30)` — returns all qualified pitchers for the season.
2. Transforms the raw FanGraphs DataFrame into `players` and `pitching_stats` shapes.
3. Upserts into PostgreSQL (bulk `executemany` for performance):
   - `players` — on conflict by `mlb_id`, updates `team` and `name_display`.
   - `pitching_stats` — on conflict by `(player_mlb_id, season)`, updates all stat columns.

**Qualification threshold:** `qual=30` (minimum innings pitched; configurable via `--qual`).

## Environment Variables

Managed via `pydantic-settings` in `backend/app/config.py`. Loaded from `.env` at the project root.

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://statbat:changeme@db:5432/statbat` | Async DB connection (backend) |
| `ANTHROPIC_API_KEY` | `""` | Anthropic Claude API key (for text-to-SQL) |
| `OPENAI_API_KEY` | `""` | OpenAI API key (fallback text-to-SQL) |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:3001` | Comma-separated allowed CORS origins |

The data pipeline reads `DATABASE_URL` from `.env` and replaces `asyncpg` with `psycopg2` for synchronous ingestion.

## Request Lifecycle

```
Browser
  └── POST /api/query { "question": "..." }
        └── generate_sql()   [stub → NotImplementedError → HTTP 501]
              └── execute_sql()
                    └── generate_answer()
                          └── QueryResponse { question, sql, result, answer }
```
