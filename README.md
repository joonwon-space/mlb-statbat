# MLB StatBat

A natural language baseball statistics query app. Ask questions in plain English — MLB StatBat converts them to SQL, queries the database, and returns a human-friendly answer.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12), SQLAlchemy async, PostgreSQL 16 |
| Frontend | Next.js (TypeScript), Tailwind CSS, shadcn/ui |
| Data Pipeline | pybaseball (FanGraphs), pandas, psycopg2 |
| LLM | Anthropic Claude (claude-haiku-4-5, text-to-SQL — live) |
| Infrastructure | Docker Compose, Cloudflare Tunnel |

## Quick Start

### Docker (recommended)

1. Copy the environment template and fill in values:

   ```bash
   cp .env.example .env   # edit DATABASE_URL, POSTGRES_*, API keys
   ```

2. Start all services:

   ```bash
   docker compose up
   ```

   Services:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API docs (Swagger): http://localhost:8000/docs

### Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Data pipeline** (ingest one season of batting and pitching stats):
```bash
cd data_pipeline
pip install -r requirements.txt
python ingest_batting.py --season 2025
python ingest_pitching.py --season 2025
```

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

Configuration is in `backend/pyproject.toml`. pytest-asyncio runs async tests automatically; pytest-cov reports coverage. `text_to_sql.py` has 100% coverage.

## Project Structure

```
mlb-statbat/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point, routes, rate limiter
│   │   ├── text_to_sql.py   # LLM-powered query generation (live, Anthropic)
│   │   ├── models.py        # SQLAlchemy models (Player, BattingStats, PitchingStats)
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── database.py      # Async DB session setup
│   │   └── config.py        # pydantic-settings environment config
│   ├── alembic/             # Alembic migration framework
│   │   ├── env.py           # Async-compatible migration environment
│   │   └── versions/        # Migration scripts
│   ├── tests/               # pytest test suite (77 tests)
│   │   ├── conftest.py      # Shared fixtures
│   │   ├── test_main.py     # Endpoint integration tests
│   │   ├── test_schemas.py  # Schema validation tests
│   │   └── test_text_to_sql.py  # text_to_sql unit tests (100% coverage)
│   ├── pyproject.toml       # pytest + coverage configuration
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/             # Next.js app router pages
│       └── lib/api.ts       # API client (queryStats)
├── data_pipeline/
│   ├── ingest_batting.py    # FanGraphs batting stats ingestion (batch upsert)
│   └── ingest_pitching.py   # FanGraphs pitching stats ingestion (batch upsert)
├── docs/
│   ├── architecture/        # Technical architecture docs
│   └── setup/              # Deployment and infrastructure guides
└── docker-compose.yml
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `POSTGRES_USER` | Yes (Docker) | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes (Docker) | PostgreSQL password |
| `POSTGRES_DB` | Yes (Docker) | PostgreSQL database name |
| `ANTHROPIC_API_KEY` | No | Anthropic Claude API key (for text-to-SQL) |
| `OPENAI_API_KEY` | No | OpenAI API key (fallback text-to-SQL) |
| `CLOUDFLARED_TOKEN` | No | Cloudflare Tunnel token (for external access) |
| `CORS_ORIGINS` | No | Comma-separated allowed CORS origins (default: `http://localhost:3000,http://localhost:3001`) |
| `NEXT_PUBLIC_API_URL` | No | Backend base URL seen by the browser (default: `http://localhost:8000`) |

Never commit `.env` to version control.

## Documentation

- [Architecture Overview](docs/architecture/overview.md) — stack, DB models, LLM pipeline, data pipeline
- [API Reference](docs/architecture/api-reference.md) — endpoint shapes and error codes
- [Frontend Guide](docs/architecture/frontend-guide.md) — page routing, key files, adding pages
- [Subdomain Setup](docs/setup/subdomain-setup.md) — Mac Mini + Docker + Cloudflare Tunnel deployment
