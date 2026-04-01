from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

# DB schema description for the LLM prompt
DB_SCHEMA = """
Tables:
- players: id, mlb_id, name_first, name_last, name_display, position, team, bats, throws
- batting_stats: id, player_mlb_id, season, team, games, plate_appearances, at_bats,
  hits, doubles, triples, home_runs, rbi, runs, stolen_bases, walks, strikeouts,
  batting_avg, obp, slg, ops, wrc_plus, war

Relationships:
- batting_stats.player_mlb_id references players.mlb_id
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


async def execute_sql(db: AsyncSession, sql: str) -> list[dict]:
    """Execute generated SQL and return rows as list of dicts."""
    result = await db.execute(text(sql))
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
