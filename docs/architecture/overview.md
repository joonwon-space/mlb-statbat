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
2. `execute_sql(db: AsyncSession, sql: str) -> list[dict]` — executes the generated SQL against PostgreSQL via SQLAlchemy async and returns rows as a list of dicts.
3. `generate_answer(question, sql, rows) -> str` — intended to call an LLM to produce a human-friendly summary of the results. Currently returns a raw string representation.

The `SYSTEM_PROMPT` embeds the full DB schema so the LLM can generate accurate SQL without needing additional context at query time.

When the LLM is not configured, `POST /api/query` returns HTTP 501.

## Data Pipeline (`data_pipeline/ingest_batting.py`)

Fetches batting stats from FanGraphs via the `pybaseball` library and upserts them into PostgreSQL.

**CLI usage:**
```bash
python ingest_batting.py --season 2025
```

**What it does:**
1. Calls `pybaseball.batting_stats(season, qual=50)` — returns all qualified batters for the season.
2. Transforms the raw FanGraphs DataFrame into `players` and `batting_stats` shapes.
3. Upserts into PostgreSQL:
   - `players` — on conflict by `mlb_id`, updates `team` and `name_display`.
   - `batting_stats` — on conflict by `(player_mlb_id, season)`, updates all stat columns.

**Qualification threshold:** `qual=50` (minimum 50 plate appearances).

## Environment Variables

Managed via `pydantic-settings` in `backend/app/config.py`. Loaded from `.env` at the project root.

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://statbat:changeme@db:5432/statbat` | Async DB connection (backend) |
| `ANTHROPIC_API_KEY` | `""` | Anthropic Claude API key (for text-to-SQL) |
| `OPENAI_API_KEY` | `""` | OpenAI API key (fallback text-to-SQL) |

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
