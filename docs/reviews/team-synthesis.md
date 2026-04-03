# Team Analysis Synthesis -- 2026-04-03 (Sprint 2)

## Executive Summary

Sprint 1 successfully addressed the most critical security gaps (SQL guard, CORS, error sanitization, input validation) and key UX improvements (example chips, loading skeleton). However, the core value proposition remains non-functional: generate_sql() and generate_answer() are still stubs raising NotImplementedError. Backend test coverage is at ~13% (25 tests, all for SQL guard). Alembic is installed but uninitialized. Sprint 2 must focus on three pillars: (1) wire LLM integration to make the app functional, (2) build the test suite to 80% coverage, (3) initialize Alembic migrations. These three items unblock everything downstream.

## Sprint 1 Completed Items

- SQL guard with sqlparse (blocks DML/DDL, multi-statement, SELECT INTO) + 25 tests
- CORS restriction to env-based origins
- Error message sanitization (no SQL errors to users)
- Input validation (min_length=3, max_length=500)
- Example question chips on frontend
- Loading skeleton/spinner
- batting_stats.season index
- print() -> logging in pipeline
- PitchingStats model + ingest_pitching.py
- Pipeline Dockerfile + docker-compose integration
- Pipeline --qual CLI arg

## Impact x Effort Matrix

### Do First (tasks.md) -- High Impact, Low/Medium Effort

| ID | Title | Source Agents | Impact | Effort |
|----|-------|--------------|--------|--------|
| PROD-011 | Wire generate_sql() to Anthropic Claude API | product, tech-debt | core-feature | M |
| PROD-011b | Wire generate_answer() for human-readable answers | product, ux | core-feature | M |
| TD-011 | Backend test suite to 80% coverage | tech-debt, product | reliability | M |
| TD-012 | Add pytest config + conftest.py with async fixtures | tech-debt | developer-experience | S |
| TD-013 | Initialize Alembic migration framework | tech-debt, product | maintainability | M |
| SEC-011 | Add SQL statement_timeout (5s) for DoS prevention | security, perf | denial-of-service | S |
| SEC-012 | Add rate limiting (slowapi) to /api/query | security | denial-of-service | S |
| TD-014/PERF-011 | Batch ingest_batting.py to match ingest_pitching.py | tech-debt, perf | pipeline-speed | S |

### Plan Carefully (todo.md P1) -- High Impact, Higher Effort

| ID | Title | Source Agents | Impact | Effort |
|----|-------|--------------|--------|--------|
| SEC-013 | Read-only DB user for query execution | security | defense-in-depth | M |
| UX-012 | Query history with localStorage | ux, product | user-experience | M |
| TD-016 | Extract shared pipeline code into common.py | tech-debt | maintainability | S |
| PERF-012 | Result set size limit (fetchmany/LIMIT) | perf, security | memory-safety | S |
| UX-016 | Column name mapping in results table | ux | data-presentation | S |
| SEC-017 | Prompt armor for LLM injection | security | defense-in-depth | M |
| PROD-015 | Player position/handedness in pipeline | product | data-completeness | S |
| PERF-015 | Add LIMIT instruction to LLM system prompt | perf | response-time | S |

### Nice to Have (todo.md P2-P3)

| ID | Title | Source Agents | Impact | Effort |
|----|-------|--------------|--------|--------|
| UX-013 | Explicit empty state for zero results | ux | user-experience | S |
| UX-014 | Textarea aria-label | ux | accessibility | S |
| UX-015 | Table accessibility (caption, scope) | ux | accessibility | S |
| SEC-014 | Non-root Docker containers | security | container-security | S |
| SEC-015 | Security headers on frontend (CSP) | security | hardening | S |
| SEC-016 | Warn on missing API keys at startup | security | developer-experience | S |
| TD-015 | Frontend test suite (vitest) | tech-debt | reliability | M |
| TD-017 | Type annotations on pipeline functions | tech-debt | developer-experience | S |
| TD-018/PERF-014 | Connection pool configuration | tech-debt, perf | scalability | S |
| UX-017 | Copy-to-clipboard for SQL | ux | user-experience | S |
| UX-018 | Dark/light mode toggle | ux | user-experience | S |
| PERF-013 | Server/client component split | perf, tech-debt | load-time | M |
| UX-011 | Better 501 error message | ux | user-experience | S |

### Skipped

| ID | Title | Reason |
|----|-------|--------|
| PROD-016 | Automated data refresh | Premature -- manual refresh fine for MVP |

## Data & Feature Completeness Snapshot

### Data Coverage (Sprint 2 vs Sprint 1)
| Area | Sprint 1 | Sprint 2 | Delta | Notes |
|------|----------|----------|-------|-------|
| Player profiles | 40% | 45% | +5% | Model complete but pipeline still doesn't extract position/handedness |
| Batting stats | 60% | 65% | +5% | Good stat set. Schema stable, but no data actually ingested |
| Pitching stats | 0% | 30% | +30% | Model + pipeline created. No data ingested yet |
| Historical depth | 10% | 10% | 0% | Pipeline supports --season but no multi-year run executed |
| Data freshness | 0% | 0% | 0% | Manual pipeline only |
| Team/league aggregates | 0% | 0% | 0% | Not started |

### Feature Completeness (Sprint 2 vs Sprint 1)
| Feature | Sprint 1 | Sprint 2 | Delta | Notes |
|---------|----------|----------|-------|-------|
| Natural language query | 30% | 35% | +5% | Endpoint + UI work. LLM still stubbed |
| Query accuracy | 0% | 0% | 0% | Cannot assess until LLM wired |
| Answer quality | 0% | 0% | 0% | Still returns str(rows) |
| Data visualization | 0% | 0% | 0% | Not started |
| Search/browse | 0% | 0% | 0% | Not started |
| Comparison tools | 0% | 0% | 0% | Not started |
| Historical trends | 0% | 0% | 0% | Not started |

## Recommended Next Milestones

1. **M1: Working Query Loop (Sprint 2)** -- Wire LLM, build test suite, init Alembic, add rate limiting + timeout. Makes the app functional and testable. Estimated: 8 tasks.
2. **M2: Data Depth + Polish (Sprint 3)** -- Ingest 5 years of data, query history, column mapping, caching, read-only DB user. Makes the app useful.
3. **M3: Public Launch (Sprint 4)** -- Security headers, non-root Docker, component extraction, visualization, prompt armor. Makes the app production-ready.

## Detailed Findings by Severity

### Critical (2)
- **PROD-011**: LLM integration still NotImplementedError stub -- core feature non-functional
- **TD-011**: Backend test coverage at 13% (target 80%)

### High (7)
- **TD-012**: No pytest configuration / conftest.py
- **TD-013**: Alembic installed but not initialized
- **SEC-011**: No SQL query execution timeout
- **SEC-012**: No rate limiting on /api/query
- **SEC-013**: No read-only DB user
- **PERF-011/TD-014**: ingest_batting.py row-by-row inserts
- **UX-011**: Developer-facing 501 error message
- **UX-012**: No query history
- **PROD-012**: No data ingested
- **PROD-013**: Test suite blocks confident deployment

### Medium (14)
- TD-014, TD-015, TD-016, SEC-014, SEC-015, SEC-016, SEC-017
- UX-013, UX-014, UX-015, UX-016, PERF-012, PERF-013, PROD-014, PROD-015

### Low (6)
- TD-017, TD-018, PERF-014, PERF-015, UX-017, UX-018, PROD-016
