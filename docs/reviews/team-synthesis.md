# Team Analysis Synthesis -- 2026-04-03

## Executive Summary

MLB StatBat is a well-structured early-stage project with ~741 lines of code, but the core value proposition (natural language baseball queries) is non-functional -- LLM integration is stubbed with NotImplementedError. The highest-priority work is completing the data pipeline and wiring up LLM integration. Security is the most urgent concern: when LLM goes live, the absence of a SQL guard means arbitrary SQL execution is possible via prompt injection. The codebase has zero test coverage, no rate limiting, wide-open CORS, and no database migration tooling. The good news: the small codebase means all issues are fixable with modest effort.

## Impact x Effort Matrix

### Do First (tasks.md) -- High Impact, Low Effort

| ID | Title | Source Agents | Impact | Effort |
|----|-------|--------------|--------|--------|
| SEC-001 | Add SQL guard (SELECT-only) on LLM-generated queries | security, perf | data-loss prevention | S |
| SEC-006 | Stop exposing SQL error messages to users | security, ux | information-disclosure | S |
| SEC-003 | Restrict CORS to known origins | security | API hardening | S |
| TD-005 | Add input validation (min/max length) to QueryRequest | tech-debt, security | reliability | S |
| UX-002 | Add example question chips for new users | ux, product | user-experience | S |
| UX-003 | Add loading skeleton/spinner for query execution | ux | user-experience | S |
| PERF-003 | Add index on batting_stats.season column | perf | response-time | S |
| TD-003 | Replace print() with logging module in pipeline | tech-debt | maintainability | S |

### Plan Carefully (todo.md P1) -- High Impact, Higher Effort

| ID | Title | Source Agents | Impact | Effort |
|----|-------|--------------|--------|--------|
| PROD-001 | Wire generate_sql() to Anthropic Claude API | product | core feature | M |
| PROD-004 | Wire generate_answer() to LLM for human-readable answers | product, ux | core feature | M |
| SEC-002 | Create read-only database user for query execution | security | defense-in-depth | M |
| SEC-004 | Add rate limiting (slowapi) to /api/query | security | DoS prevention | M |
| TD-001 | Add test suite -- backend pytest + frontend tests | tech-debt | reliability | M |
| TD-004 | Set up Alembic migrations, remove create_all() | tech-debt | maintainability | M |
| PERF-001/TD-002 | Batch data pipeline inserts (executemany) | perf, tech-debt | pipeline speed | M |
| PERF-002 | Add LLM response caching (TTLCache) | perf | response-time, cost | M |
| PROD-003 | Multi-season historical data ingestion (2020-2025) | product | data-completeness | S |
| UX-001 | Add query history with localStorage persistence | ux, product | user-experience | M |

### Nice to Have (todo.md P2-P3)

| ID | Title | Source Agents | Impact | Effort |
|----|-------|--------------|--------|--------|
| UX-004 | Human-readable column headers in results table | ux | data-presentation | S |
| UX-005 | Number formatting for baseball stats (.300 avg) | ux | data-presentation | S |
| UX-006 | Add aria-label to query textarea | ux | accessibility | S |
| UX-007 | Add table caption and scope for a11y | ux | accessibility | S |
| PERF-005 | LLM response streaming (SSE) | perf | perceived speed | L |
| PERF-006 | Split page.tsx into server + client components | perf, tech-debt | load-time | M |
| PROD-006 | Fielding stats, team standings, league averages | product | data-completeness | L |
| PROD-007 | Data visualization (charts for leaderboards/trends) | product | user-value | L |
| TD-009 | Extract page.tsx into smaller components | tech-debt | maintainability | M |
| SEC-009 | Non-root Docker users | security | container security | S |

### Skipped

| ID | Title | Reason |
|----|-------|--------|
| TD-008 | Dual DB driver (asyncpg vs psycopg2) | Working as designed; low risk at current scale |
| TD-010 | No .env.example | Already tracked in todo.md P0 |
| PERF-007 | Full DataFrame in memory | Only relevant for 20+ season batch loads |
| UX-009 | Mobile table scroll indicator | Nice to have, not impactful yet |

## Data & Feature Completeness Snapshot

### Data Coverage
| Area | Coverage | Notes |
|------|----------|-------|
| Player profiles | 40% | Name, team only. Missing position, bats, throws from pipeline |
| Batting stats | 60% | Good stat set, but only single-season data likely ingested |
| Pitching stats | 0% | Model not created yet (in tasks.md) |
| Historical depth | 10% | Script supports --season but no multi-year workflow |
| Data freshness | 0% | No automated refresh; manual pipeline only |
| Team/league aggregates | 0% | No standings, league averages, or team totals |

### Feature Completeness
| Feature | Coverage | Notes |
|---------|----------|-------|
| Natural language query | 30% | Endpoint exists, UI works, but LLM is stubbed |
| Query accuracy | 0% | Cannot assess until LLM is wired |
| Answer quality | 0% | Returns raw Python dict |
| Data visualization | 0% | Text table only |
| Search/browse | 0% | No player/team browsing |
| Comparison tools | 0% | No side-by-side comparison |
| Historical trends | 0% | No trend analysis or charts |

## Recommended Next Milestones

1. **M1: End-to-End Query Loop (MVP)** -- Wire LLM, add SQL guard, ingest 5 years of batting data. This makes the app actually usable and testable. Estimated: 3-5 tasks.
2. **M2: Pitching Stats + Query Quality** -- Double question coverage, add history, example questions, caching. Estimated: 5-7 tasks.
3. **M3: Polish + Public Launch** -- CORS, rate limiting, Alembic, number formatting, basic charts. Estimated: 6-8 tasks.

## Detailed Findings

### Critical (3)
- **SEC-001**: No SQL guard on execute_sql() -- arbitrary SQL execution possible via LLM prompt injection
- **SEC-002**: No read-only DB user -- LLM queries run with full DDL/DML privileges
- **PROD-001**: LLM integration is NotImplementedError stub -- core feature non-functional

### High (10)
- **SEC-003**: CORS allows all origins
- **SEC-004**: No rate limiting on /api/query
- **SEC-005**: No query execution timeout
- **SEC-006**: SQL errors exposed to users
- **TD-001**: Zero test coverage
- **TD-002/PERF-001**: Row-by-row pipeline inserts
- **TD-004**: create_all() instead of Alembic
- **UX-001**: No query history
- **UX-002**: No example questions
- **UX-003**: Loading indicator is just "..."
- **PROD-003**: No historical data depth
- **PROD-004**: Answer is raw str(rows)

### Medium (15)
- TD-003, TD-005, TD-006, TD-007, SEC-007, SEC-008, SEC-009, SEC-010
- UX-004, UX-005, UX-006, UX-007, UX-008, UX-010
- PERF-002, PERF-003, PERF-004, PERF-005, PERF-006
- PROD-005, PROD-006, PROD-007

### Low (4)
- TD-008, TD-009, TD-010, PERF-007, PROD-008
