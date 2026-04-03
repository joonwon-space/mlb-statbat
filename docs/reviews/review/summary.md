# Code Review Summary - Sprint 2 (branch: auto-task/20260403-1301)

## Verdict: REQUEST CHANGES

Sprint 2 delivered substantial, well-intentioned work: a comprehensive test suite (74 tests across 4 files), Alembic migration framework wired to async SQLAlchemy, rate limiting, SQL execution timeout, batch upsert in the data pipeline, and both LLM integrations fully wired to Anthropic Claude. The security posture is meaningfully improved over the prior state. However, five HIGH-severity findings require fixes before this branch merges to main.

---

## Must Fix (before merge)

| # | ID | Title | Severity | Reviewers | Location | Fix |
|---|-----|-------|----------|-----------|----------|-----|
| 1 | COR-001 | SET LOCAL statement_timeout not guaranteed inside transaction | HIGH | Correctness + Security | backend/app/text_to_sql.py:115 | Wrap both SET LOCAL and the SELECT in async with db.begin() to ensure they share a transaction. Without this the 5-second guard is unreliable. |
| 2 | SEC-001 | SQL guard does not block pg_sleep() or CROSS JOIN DoS via valid SELECT | HIGH | Security | backend/app/text_to_sql.py:80-101 | Add a denylist of dangerous PostgreSQL functions (pg_sleep, lo_export, dblink) in _validate_select_only. Enforce LIMIT 1000 if no LIMIT token is present. |
| 3 | PERF-001 | execute_sql fetches entire result set into memory with no row cap | HIGH | Performance | backend/app/text_to_sql.py:120-121 | Replace fetchall() with fetchmany(1000) or enforce LIMIT at SQL level. |
| 4 | SEC-002 | Hardcoded default DATABASE_URL with password changeme in config.py | HIGH | Security | backend/app/config.py:5 | Remove the default value: database_url: str (no default). Add startup guard detecting changeme. |
| 5 | COR-002 | generate_answer() failure not caught in main.py | HIGH | Correctness | backend/app/main.py:74 | Wrap the generate_answer call in try/except; degrade gracefully to str(rows) on failure. |

---

## Should Fix (before or soon after merge)

| # | ID | Title | Severity | Reviewer | Location | Fix |
|---|-----|-------|----------|----------|----------|-----|
| 6 | SEC-003 | Rate limiter vulnerable to IP spoofing via X-Forwarded-For | MEDIUM | Security | backend/app/main.py:19 | Configure trusted proxy validation before honoring X-Forwarded-For. |
| 7 | SEC-004 + MAIN-003 | ingest_batting.py builds SQL from DataFrame columns without whitelist check | MEDIUM | Security + Maintainability | data_pipeline/ingest_batting.py:112-128 | Add allowed = set(COLUMN_MAP.values()); assert set(stat_cols).issubset(allowed) before building INSERT SQL. |
| 8 | MAIN-001 | text_to_sql.py mixes four concerns in one file - violates SRP | HIGH | Maintainability | backend/app/text_to_sql.py:1-178 | Extract app/sql_validator.py and app/llm_client.py. Keep text_to_sql.py as thin orchestration. |
| 9 | MAIN-005 + PERF-004 | Alembic migration missing FK constraints on batting_stats and pitching_stats | MEDIUM | Maintainability + Performance | backend/alembic/versions/0001_initial_schema.py:62-103 | Add sa.ForeignKeyConstraint to both tables before data is loaded. |
| 10 | COR-003 + PERF-003 | Anthropic client re-instantiated on every request | MEDIUM | Correctness + Performance | backend/app/text_to_sql.py:62,167 | Create a module-level singleton initialized lazily on first use. |
| 11 | MAIN-004 | config.py default credentials make misconfiguration silent | MEDIUM | Maintainability | backend/app/config.py:5-6 | Add model_validator that logs WARNING when anthropic_api_key is empty at startup. |

---

## Consider (optional improvements)

| # | ID | Title | Severity | Reviewer | Location | Fix |
|---|-----|-------|----------|----------|----------|-----|
| 12 | SEC-005 | No content filtering for LLM prompt injection attempts | MEDIUM | Security | backend/app/text_to_sql.py:51-77 | Strip control characters; log requests containing injection phrases. |
| 13 | COR-004 | Name split produces empty name_last for single-word player names | MEDIUM | Correctness | data_pipeline/ingest_batting.py:74 | Use name_parts.get(1).fillna('') and log a warning when name_last is empty. |
| 14 | COR-005 | _validate_select_only passes SELECT 1; with trailing semicolon | MEDIUM | Correctness | backend/app/text_to_sql.py:87-95 | Strip trailing semicolons before sqlparse. |
| 15 | PERF-002 | No caching for identical LLM questions - two API calls per identical request | MEDIUM | Performance | backend/app/text_to_sql.py:51-77 | Add TTLCache(maxsize=500, ttl=3600) for generate_sql() keyed on normalized question. |
| 16 | MAIN-002 | SYSTEM_PROMPT eagerly evaluated as f-string at import | MEDIUM | Maintainability | backend/app/text_to_sql.py:29-34 | Convert to def _build_system_prompt(schema: str = DB_SCHEMA) -> str. |
| 17 | COR-006 | conftest.py async fixture has incorrect return type annotation | LOW | Correctness | backend/tests/conftest.py:12 | Change -> AsyncClient to -> AsyncGenerator[AsyncClient, None]. |
| 18 | MAIN-006 | Private helpers directly imported in tests | LOW | Maintainability | backend/tests/test_text_to_sql.py:5-10 | Add __all__ to text_to_sql.py or document the intentional direct testing. |
| 19 | MAIN-007 | mock_db fixture in conftest.py is unused dead code | LOW | Maintainability | backend/tests/conftest.py:32-39 | Remove or update to support the two-call side_effect pattern. |

---

## Review Statistics

| Reviewer | Verdict | Findings |
|----------|---------|----------|
| Correctness | request-changes | 6 findings (2 HIGH, 3 MEDIUM, 1 LOW) |
| Security | request-changes | 5 findings (2 HIGH, 3 MEDIUM) |
| Performance | request-changes | 5 findings (1 HIGH, 2 MEDIUM, 2 LOW) |
| Maintainability | request-changes | 7 findings (1 HIGH, 4 MEDIUM, 2 LOW) |
| Total unique findings | | 19 (after deduplication of 4 overlapping pairs) |

Must Fix: 5 items (blocks merge)
Should Fix: 6 items
Consider: 8 items

---

## Key Strengths

- Comprehensive test suite (74 tests, good edge case and boundary value coverage)
- _validate_select_only guard with sqlparse blocks multi-statement injection, DML, DDL, SELECT INTO
- Alembic async env.py correctly implemented; replaces create_all() appropriately
- Batch upsert in ingest_batting.py is a clean improvement over row-by-row iteration
- Rate limiting in place with appropriate 429 handler registration
- Error messages are safe - no raw exception details leaked to clients for DB errors

## Critical Risk Summary

The most urgent risks:

1. Timeout guard unreliable (COR-001 + SEC-001): The 5-second SET LOCAL statement_timeout may not apply without an explicit transaction. Even when it does, pg_sleep() and large CROSS JOIN queries bypass the intent. Fixing COR-001 (explicit transaction) plus adding LIMIT enforcement plus the pg_sleep denylist addresses both risks in one pass.

2. Unbounded fetchall() (PERF-001): Even with a timeout, a query returning 50k rows loads everything into Python memory before any cap is applied.
