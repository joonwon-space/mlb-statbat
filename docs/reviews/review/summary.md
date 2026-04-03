# Code Review Summary

**Branch**: `auto-task/20260403-1120`
**Date**: 2026-04-03
**Re-review after 4 fixes**: sqlparse SQL guard, 25 tests, logging migration, bulk executemany

## Verdict: REQUEST CHANGES

Three reviewers (correctness, security, maintainability) recommend request-changes due to one HIGH finding that persists after the fixes: the sqlparse SQL guard passes `SELECT INTO new_table FROM ...` as a valid SELECT, allowing a destructive DDL variant through. The performance reviewer approves. Two medium findings also carry over unaddressed from the prior cycle.

---

## Fix Verification

The 4 applied fixes are confirmed working:

| Fix | Status | Notes |
|-----|--------|-------|
| SQL guard now uses sqlparse | RESOLVED for semicolon injection | HIGH gap remains: SELECT INTO passes as type='SELECT' |
| 25 tests for _validate_select_only() | CONFIRMED passing | test_select_into_blocked is a no-op assertion (try/except/pass) |
| ingest_pitching.py print() replaced with logging | FULLY RESOLVED | Matches ingest_batting.py convention |
| N+1 INSERT replaced with bulk executemany | FULLY RESOLVED | Both player and stats upserts now use executemany |

---

## Must Fix (before merge)

| # | ID | Title | Severity | Reviewers | Location | Fix |
|---|-----|-------|----------|-----------|----------|-----|
| 1 | COR-001 / SEC-001 | SELECT INTO passes SQL guard — destructive DDL variant allowed | HIGH | correctness, security | `backend/app/text_to_sql.py:55-68` | After confirming `stmt_type == 'SELECT'`, scan flattened tokens for `INTO` keyword outside subquery: `if any(t.ttype is sqlparse.tokens.Keyword and t.normalized == 'INTO' for t in stmt.flatten()): raise ValueError('SELECT INTO is not permitted')`. Update `test_select_into_blocked` to `pytest.raises(ValueError)`. |

---

## Should Fix (before or soon after merge)

| # | ID | Title | Severity | Reviewer | Location | Fix |
|---|-----|-------|----------|----------|----------|-----|
| 2 | COR-002 / SEC-002 | Dynamic SQL column names not whitelist-validated in ingest_pitching.load() | MEDIUM | correctness, security | `data_pipeline/ingest_pitching.py:107-121` | Add: `import re; invalid = [c for c in stat_cols if not re.match(r'^[a-z_][a-z0-9_]*$', c)]; if invalid: raise ValueError(f'Unsafe column names: {invalid}')` before building the f-string SQL. |
| 3 | PERF-001 | Unbounded fetchall() — no row cap on execute_sql() results | MEDIUM | performance | `backend/app/text_to_sql.py:76-78` | Replace `result.fetchall()` with `result.fetchmany(1000)`. Add `LIMIT 100` guidance to `SYSTEM_PROMPT`. |
| 4 | MAIN-001 | test_select_into_blocked is a no-op assertion — guard regression not caught | MEDIUM | maintainability | `backend/tests/test_text_to_sql.py:113-125` | Document current behavior explicitly OR fix the guard (COR-001) and change to `pytest.raises(ValueError)`. Either way, remove the try/except/pass that masks the assertion. |
| 5 | MAIN-002 | cors_origins_list @property non-idiomatic for pydantic-settings v2 | MEDIUM | maintainability | `backend/app/config.py:10` | Use `@computed_field` from pydantic v2: `from pydantic import computed_field; @computed_field; @property; def cors_origins_list(self) -> list[str]: ...` |
| 6 | MAIN-003 | generate_answer() stub returns raw Python repr visible to end users | MEDIUM | maintainability | `backend/app/text_to_sql.py:81-86` | Return: `f'Found {len(rows)} result(s). (Natural language answers will be available once LLM integration is configured.)'` |
| 7 | SEC-003 | No rate limiting on /api/query endpoint | MEDIUM | security | `backend/app/main.py:47` | Add `slowapi` rate limiting: `@limiter.limit('10/minute')` on the query endpoint. Required by project security checklist. |

---

## Consider (optional improvements)

| # | ID | Title | Severity | Reviewer | Location | Fix |
|---|-----|-------|----------|----------|----------|-----|
| 8 | COR-003 | Missing .copy() in transform() stats branch on normal code path | LOW | correctness | `data_pipeline/ingest_pitching.py:80-87` | Always copy after rename: `stats = df[list(available.keys())].rename(columns=available).copy()` |
| 9 | MAIN-004 | load() handles two responsibilities without helper extraction | LOW | maintainability | `data_pipeline/ingest_pitching.py:93-125` | Extract `_upsert_players(conn, records)` and `_upsert_stats(conn, records, stat_cols)` helpers. |
| 10 | PERF-002 | sqlparse.parse() runs synchronously in async hot path | LOW | performance | `backend/app/text_to_sql.py:55-68` | Wrap in `run_in_executor` to avoid blocking event loop. Defer until profiling confirms impact. |
| 11 | PERF-003 | Loading skeleton flickers on fast responses — no minimum display threshold | LOW | performance | `frontend/src/app/page.tsx:101` | Delay skeleton 300ms via `useEffect` + `setTimeout` before setting `showSkeleton = true`. |
| 12 | SEC-004 | Full SQL query text logged on exception — may expose user data in log aggregation | LOW | security | `backend/app/text_to_sql.py:72-75` | Log truncated preview: `logger.exception('SQL execution failed (query_len=%d, preview=%s)', len(sql), sql[:100])` |

---

## Positive Findings (confirmed by re-review)

- **Semicolon injection blocked**: `_validate_select_only()` correctly uses sqlparse to enforce exactly one statement — the prior regex approach is fully replaced.
- **25 tests for SQL guard**: Comprehensive coverage of DML/DDL blocking, multi-statement injection, empty input, whitespace, CTE/WITH, subqueries, case-insensitivity. Good test structure.
- **logging in ingest_pitching.py**: Uses `logging.basicConfig` + `logger = logging.getLogger(__name__)` — fully consistent with `ingest_batting.py`.
- **Bulk executemany**: Both player upsert and pitching stats upsert now use a single `conn.execute(text(...), list_of_dicts)` call — N+1 pattern fully eliminated.
- **Error handling in execute_sql()**: The try/except wraps only the DB call, logs with `logger.exception`, and re-raises — correct pattern.
- **main.py error routing**: `ValueError` from the SQL guard is surfaced as 400 with the guard message (safe); generic `Exception` returns a sanitized 500 message — well-structured.

---

## Review Statistics

| Reviewer | Verdict | Findings |
|----------|---------|----------|
| correctness | request-changes | 3 findings |
| security | request-changes | 4 findings |
| performance | request-changes | 3 findings |
| maintainability | request-changes | 4 findings |
| **Total unique** | **REQUEST CHANGES** | **12 findings (after dedup)** |

Deduplication applied:
- COR-001 + SEC-001 merged (SELECT INTO passes SQL guard — same root cause)
- COR-002 + SEC-002 merged (dynamic column names not whitelisted)

**Must Fix**: 1 item (blocks merge)
**Should Fix**: 6 items
**Consider**: 5 items
