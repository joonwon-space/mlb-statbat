# MLB StatBat — Architecture Overview

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python), SQLAlchemy async, PostgreSQL |
| Frontend | Next.js (TypeScript), Tailwind CSS, shadcn/ui |
| Data Pipeline | pybaseball (FanGraphs), pandas, psycopg2 |
| LLM | Anthropic Claude (claude-haiku-4-5, text-to-SQL — live) |
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

**Status: live — wired to Anthropic Claude (claude-haiku-4-5).**

Four functions handle the query pipeline:

1. `generate_sql(question: str) -> str` — calls Anthropic Claude with `SYSTEM_PROMPT` (which embeds the full DB schema) and returns a SELECT query. Strips optional markdown fences from the model response. Raises `NotImplementedError` when `ANTHROPIC_API_KEY` is not set; raises `ValueError` if the model returns an empty response.
2. `_validate_select_only(sql: str) -> None` — SQL guard (using `sqlparse`) that enforces:
   - Exactly one statement (no semicolon-based multi-statement injection).
   - That statement is a SELECT (no DML/DDL).
   - `SELECT INTO` is blocked (creates a table despite being classified as SELECT).
   - The following PostgreSQL functions are blocked by name: `PG_SLEEP`, `DBLINK`, `LO_IMPORT`, `LO_EXPORT`, `PG_READ_FILE`, `PG_WRITE_FILE`, `PG_TERMINATE_BACKEND`, `PG_CANCEL_BACKEND`.
   - Raises `ValueError` on any violation, surfaced as HTTP 400.
3. `execute_sql(db: AsyncSession, sql: str) -> list[dict]` — calls `_validate_select_only`, then opens an explicit transaction, sets `SET LOCAL statement_timeout = 5000` (5-second hard limit), executes the SQL, and returns up to 1 000 rows as a list of dicts (`fetchmany(1000)`). DB errors are logged internally; the caller receives a generic HTTP 500.
4. `generate_answer(question, sql, rows) -> str` — calls Anthropic Claude to produce a concise 1–3 sentence human-friendly summary of the query results. Truncates large result sets to 20 rows in the prompt to avoid context blowout. Falls back to `str(rows)` when `ANTHROPIC_API_KEY` is not set or rows is empty.

The `SYSTEM_PROMPT` embeds the full DB schema (players, batting_stats, pitching_stats) so the LLM can generate accurate SQL without needing additional context at query time.

When `ANTHROPIC_API_KEY` is not configured, `POST /api/query` returns HTTP 501.

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
3. Upserts into PostgreSQL (bulk `executemany` via `to_dict("records")` for performance):
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
| `DATABASE_URL` | **required** | Async DB connection string (`postgresql+asyncpg://...`) |
| `ANTHROPIC_API_KEY` | `""` | Anthropic Claude API key (for text-to-SQL; endpoint returns 501 if absent) |
| `OPENAI_API_KEY` | `""` | OpenAI API key (reserved; not yet used) |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:3001` | Comma-separated allowed CORS origins |

The data pipeline reads `DATABASE_URL` from `.env` and replaces `asyncpg` with `psycopg2` for synchronous ingestion.

## Schema Migrations

Schema is managed by **Alembic** (`backend/alembic/`). `create_all()` is not called at startup.

```bash
# Apply all pending migrations
cd backend && alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description"
```

The async `env.py` uses `run_sync` so Alembic can introspect the async SQLAlchemy engine.

## Request Lifecycle

```
Browser
  └── POST /api/query { "question": "..." }   [rate limit: 10 req/min per IP]
        └── generate_sql()   → Anthropic Claude (claude-haiku-4-5)
              └── _validate_select_only()   → HTTP 400 on violation
                    └── execute_sql()   → 5s timeout, max 1 000 rows
                          └── generate_answer()   → Anthropic Claude summary
                                └── QueryResponse { question, sql, result, answer }
```
