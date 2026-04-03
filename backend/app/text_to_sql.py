import logging
import re

import anthropic
import sqlparse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

# DB schema description for the LLM prompt
DB_SCHEMA = """
Tables:
- players: id, mlb_id, name_first, name_last, name_display, position, team, bats, throws
- batting_stats: id, player_mlb_id, season, team, games, plate_appearances, at_bats,
  hits, doubles, triples, home_runs, rbi, runs, stolen_bases, walks, strikeouts,
  batting_avg, obp, slg, ops, wrc_plus, war
- pitching_stats: id, player_mlb_id, season, team, games, games_started,
  innings_pitched, wins, losses, saves, strikeouts, walks, home_runs_allowed,
  era, whip, fip, xfip, k_per_9, bb_per_9, hr_per_9, war

Relationships:
- batting_stats.player_mlb_id references players.mlb_id
- pitching_stats.player_mlb_id references players.mlb_id
"""

SYSTEM_PROMPT = f"""You are a SQL assistant for an MLB statistics database (PostgreSQL).
Given a natural language question about baseball stats, generate a single SELECT query.
Return ONLY the SQL query, no explanation, no markdown fences.

{DB_SCHEMA}
"""

# Model used for SQL generation (cheapest capable Anthropic model).
_SQL_MODEL = "claude-haiku-4-5"

# Regex to strip optional ```sql ... ``` markdown fences from LLM output.
_SQL_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _strip_sql_fence(raw: str) -> str:
    """Remove markdown code fences if the model wraps its response in them."""
    match = _SQL_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


async def generate_sql(question: str) -> str:
    """Call Anthropic Claude to convert a natural language question to SQL.

    Raises:
        NotImplementedError: When ANTHROPIC_API_KEY is not configured.
        anthropic.APIError: On API communication failures.
        ValueError: If the model returns an empty response.
    """
    if not settings.anthropic_api_key:
        raise NotImplementedError("LLM integration not yet configured")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=_SQL_MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}],
    )

    raw_sql = message.content[0].text if message.content else ""
    sql = _strip_sql_fence(raw_sql)

    if not sql:
        raise ValueError("LLM returned an empty SQL response")

    logger.debug("Generated SQL for %r: %s", question, sql)
    return sql


def _validate_select_only(sql: str) -> None:
    """Raise ValueError if sql contains any non-SELECT statement.

    Uses sqlparse to properly parse the SQL and verify:
    1. Exactly one statement (no multi-statement injection via semicolons)
    2. That single statement is a SELECT (not DML/DDL)
    """
    parsed = sqlparse.parse(sql)
    # Filter out empty/whitespace-only statements
    statements = [s for s in parsed if s.get_type() is not None]
    if len(statements) != 1:
        raise ValueError("Exactly one SQL statement is allowed")
    stmt = statements[0]
    stmt_type = stmt.get_type()
    if stmt_type != "SELECT":
        raise ValueError("Only SELECT queries are permitted")
    # Block SELECT INTO — sqlparse classifies it as SELECT but it creates a table
    if any(
        t.ttype is sqlparse.tokens.Keyword and t.normalized == "INTO"
        for t in stmt.flatten()
    ):
        raise ValueError("SELECT INTO is not permitted")
    # Block dangerous PostgreSQL functions (DoS vectors)
    sql_upper = sql.upper()
    _BLOCKED_FUNCTIONS = [
        "PG_SLEEP", "DBLINK", "LO_IMPORT", "LO_EXPORT",
        "PG_READ_FILE", "PG_WRITE_FILE", "PG_TERMINATE_BACKEND",
        "PG_CANCEL_BACKEND",
    ]
    for func in _BLOCKED_FUNCTIONS:
        if func in sql_upper:
            raise ValueError(f"Function {func} is not permitted")


_MAX_RESULT_ROWS = 1000  # Hard cap on returned rows to prevent memory blowout.


async def execute_sql(db: AsyncSession, sql: str) -> list[dict]:
    """Execute generated SQL and return rows as list of dicts.

    Only SELECT queries are allowed. Raises ValueError for any other statement.
    A 5-second statement timeout is enforced inside an explicit transaction
    so that SET LOCAL takes effect.
    Results are capped at _MAX_RESULT_ROWS to prevent memory exhaustion.
    """
    _validate_select_only(sql)
    try:
        async with db.begin():
            await db.execute(text("SET LOCAL statement_timeout = 5000"))
            result = await db.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchmany(_MAX_RESULT_ROWS)
    except Exception:
        logger.exception("SQL execution failed for query: %s", sql)
        raise
    return [dict(zip(columns, row)) for row in rows]


_ANSWER_SYSTEM_PROMPT = """\
You are a knowledgeable baseball analyst. Given a user question, the SQL query that was run,
and the query results, provide a concise, human-friendly answer in plain English.
Focus on the key insight; keep it to 1-3 sentences.
"""

_MAX_ROWS_IN_PROMPT = 20  # Avoid bloating the context with huge result sets.


async def generate_answer(question: str, sql: str, rows: list[dict]) -> str:
    """Call Anthropic Claude to summarise SQL query results as a natural language answer.

    Falls back gracefully when ANTHROPIC_API_KEY is not configured or when
    there are no result rows.

    Args:
        question: The original user question.
        sql: The SQL that was executed.
        rows: The rows returned by execute_sql().

    Returns:
        A human-readable summary string.
    """
    if not rows:
        return "No results found for your question."

    if not settings.anthropic_api_key:
        # Graceful degradation — return a basic string representation.
        return str(rows)

    # Truncate to avoid context blowout for very large result sets.
    display_rows = rows[:_MAX_ROWS_IN_PROMPT]
    omitted = len(rows) - len(display_rows)
    rows_text = str(display_rows)
    if omitted:
        rows_text += f"\n... and {omitted} more rows (omitted for brevity)"

    user_content = (
        f"Question: {question}\n\n"
        f"SQL executed:\n{sql}\n\n"
        f"Results ({len(rows)} row(s)):\n{rows_text}"
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=_SQL_MODEL,
        max_tokens=256,
        system=_ANSWER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    answer = message.content[0].text.strip() if message.content else str(rows)
    logger.debug("Generated answer for %r: %s", question, answer)
    return answer
