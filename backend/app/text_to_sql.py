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


async def execute_sql(db: AsyncSession, sql: str) -> list[dict]:
    """Execute generated SQL and return rows as list of dicts.

    Only SELECT queries are allowed. Raises ValueError for any other statement.
    A 5-second statement timeout is enforced at the session level so that
    runaway LLM-generated queries cannot hold a connection indefinitely.
    """
    _validate_select_only(sql)
    try:
        # Apply a per-statement timeout (5 000 ms) before running the query.
        # SET LOCAL is scoped to the current transaction block only.
        await db.execute(text("SET LOCAL statement_timeout = 5000"))
        result = await db.execute(text(sql))
    except Exception:
        logger.exception("SQL execution failed for query: %s", sql)
        raise
    columns = list(result.keys())
    return [dict(zip(columns, row)) for row in result.fetchall()]


async def generate_answer(question: str, sql: str, rows: list[dict]) -> str:
    """Call LLM to generate a human-friendly answer from the SQL results.

    Currently a stub — will be wired to LLM in the next task.
    """
    # TODO: implement LLM call to summarize results
    if not rows:
        return "No results found for your question."
    return str(rows)
