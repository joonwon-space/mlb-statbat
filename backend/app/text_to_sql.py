import logging

import sqlparse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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
Return ONLY the SQL query, no explanation.

{DB_SCHEMA}
"""


async def generate_sql(question: str) -> str:
    """Call LLM to convert natural language question to SQL.

    Currently a stub — will be wired to OpenAI or Anthropic API.
    """
    # TODO: implement LLM call
    # Example using Anthropic:
    # import anthropic
    # client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    # message = await client.messages.create(
    #     model="claude-sonnet-4-20250514",
    #     max_tokens=512,
    #     system=SYSTEM_PROMPT,
    #     messages=[{"role": "user", "content": question}],
    # )
    # return message.content[0].text.strip()

    raise NotImplementedError("LLM integration not yet configured")


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
    """
    _validate_select_only(sql)
    try:
        result = await db.execute(text(sql))
    except Exception:
        logger.exception("SQL execution failed for query: %s", sql)
        raise
    columns = list(result.keys())
    return [dict(zip(columns, row)) for row in result.fetchall()]


async def generate_answer(question: str, sql: str, rows: list[dict]) -> str:
    """Call LLM to generate a human-friendly answer from the SQL results.

    Currently a stub.
    """
    # TODO: implement LLM call to summarize results
    if not rows:
        return "No results found for your question."
    return str(rows)
