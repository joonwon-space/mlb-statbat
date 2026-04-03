# Release Readiness Report

**Branch:** `auto-task/20260403-1120`
**Date:** 2026-04-03
**Decision:** CONDITIONAL

---

## Verdict Summary

| Check          | Verdict | Details                                      |
|----------------|---------|----------------------------------------------|
| Build          | PASS    | Frontend + backend build clean, zero errors   |
| Tests          | WARN    | 25/25 passed, but only 13% coverage           |
| Migrations     | WARN    | No Alembic configured; using create_all()     |
| API Contract   | PASS    | Frontend/backend schemas aligned, no breaking changes |

## Decision: CONDITIONAL

This release is **safe to deploy to staging/dev** environments. The code builds cleanly, all existing tests pass, and API contracts are consistent. However, two conditions should be addressed before production deployment:

### Conditions

1. **Test coverage is critically low (13%)** — Only the SQL guard has tests (25 tests, all passing). Core modules (main.py, models.py, schemas.py, config.py, database.py) have zero coverage. Recommend adding integration tests for the `/api/query` endpoint before production.

2. **No Alembic migration framework** — Schema management relies on `Base.metadata.create_all()` which cannot handle ALTER operations on existing tables. This is acceptable for initial deployment but must be set up before any future schema changes.

### Non-blocking observations

- No frontend test suite configured (no test script in package.json)
- `player_mlb_id` columns lack ForeignKey constraints (referential integrity not enforced at DB level)
- Frontend error response type not formally defined (works correctly in practice)

---

## Release Notes

### Changes in `auto-task/20260403-1120` (19 commits)

#### Features
- **Pitching stats support**: New PitchingStats ORM model, ingest pipeline (`ingest_pitching.py`), and DB_SCHEMA update in text_to_sql.py
- **Data pipeline Docker service**: New Dockerfile and docker-compose service with pipeline profile
- **Example question chips**: Interactive example question buttons on the main page (UX-002)
- **CLI improvements**: Added `--qual` CLI argument to ingest_batting.py (default 50)

#### Security
- **SQL injection guard**: SELECT-only SQL guard in `execute_sql()` with sqlparse-based semicolon bypass fix
- **SELECT INTO blocked**: Additional guard against SELECT INTO statements
- **CORS hardening**: Restricted CORS to env-configured origins only (SEC-003)
- **Input validation**: Added min_length=3 / max_length=500 to QueryRequest (SEC-007)
- **Error sanitization**: SQL error messages sanitized, internal details logged only (SEC-006)

#### Performance
- **Bulk insert**: Replaced N+1 INSERT with bulk executemany in ingest_pitching.py

#### Code Quality
- **Logging**: Replaced print() with logging module in ingest_batting.py and ingest_pitching.py
- **Tests**: 25 new tests for SQL guard `_validate_select_only()`

#### Docs & Chores
- Updated frontend metadata title/description
- Task tracking updates (loading skeleton, batting_stats index marked done)

---

## Detailed Reports

- [Build Validator](./build-validator.json)
- [Test Runner](./test-runner.json)
- [Migration Checker](./migration-checker.json)
- [API Contract Checker](./api-contract-checker.json)
