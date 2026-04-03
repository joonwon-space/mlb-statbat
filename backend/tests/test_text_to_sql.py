import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from app.text_to_sql import (
    _strip_sql_fence,
    _validate_select_only,
    execute_sql,
    generate_answer,
    generate_sql,
)


class TestValidateSelectOnly:
    """Tests for the SQL guard that prevents non-SELECT execution."""

    # --- Valid SELECT queries (should pass) ---

    def test_simple_select(self) -> None:
        _validate_select_only("SELECT * FROM players")

    def test_select_with_where(self) -> None:
        _validate_select_only("SELECT name FROM players WHERE id = 1")

    def test_select_with_join(self) -> None:
        _validate_select_only(
            "SELECT p.name, b.home_runs FROM players p "
            "JOIN batting_stats b ON p.mlb_id = b.player_mlb_id"
        )

    def test_select_with_subquery(self) -> None:
        _validate_select_only(
            "SELECT * FROM players WHERE mlb_id IN (SELECT player_mlb_id FROM batting_stats)"
        )

    def test_select_with_cte(self) -> None:
        _validate_select_only(
            "WITH top_hitters AS (SELECT * FROM batting_stats WHERE home_runs > 30) "
            "SELECT * FROM top_hitters"
        )

    def test_select_with_aggregate(self) -> None:
        _validate_select_only(
            "SELECT team, AVG(batting_avg) FROM batting_stats GROUP BY team HAVING AVG(batting_avg) > .270"
        )

    def test_select_with_order_limit(self) -> None:
        _validate_select_only(
            "SELECT * FROM batting_stats ORDER BY home_runs DESC LIMIT 10"
        )

    def test_select_case_insensitive(self) -> None:
        _validate_select_only("select * from players")

    def test_select_with_leading_whitespace(self) -> None:
        _validate_select_only("   SELECT * FROM players")

    # --- Blocked: multi-statement injection ---

    def test_semicolon_injection_drop(self) -> None:
        with pytest.raises(ValueError, match="one SQL statement"):
            _validate_select_only("SELECT * FROM players; DROP TABLE players")

    def test_semicolon_injection_delete(self) -> None:
        with pytest.raises(ValueError, match="one SQL statement"):
            _validate_select_only("SELECT 1; DELETE FROM players")

    def test_semicolon_injection_update(self) -> None:
        with pytest.raises(ValueError, match="one SQL statement"):
            _validate_select_only("SELECT 1; UPDATE players SET name='x'")

    def test_multiple_selects(self) -> None:
        with pytest.raises(ValueError, match="one SQL statement"):
            _validate_select_only("SELECT 1; SELECT 2")

    # --- Blocked: non-SELECT single statements ---

    def test_drop_table(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            _validate_select_only("DROP TABLE players")

    def test_delete(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            _validate_select_only("DELETE FROM players")

    def test_update(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            _validate_select_only("UPDATE players SET name = 'x'")

    def test_insert(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            _validate_select_only("INSERT INTO players VALUES (1, 'x')")

    def test_alter(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            _validate_select_only("ALTER TABLE players ADD COLUMN age INT")

    def test_truncate(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            _validate_select_only("TRUNCATE TABLE players")

    def test_create(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            _validate_select_only("CREATE TABLE evil (id INT)")

    def test_grant(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            _validate_select_only("GRANT ALL ON players TO public")

    # --- Blocked: empty / whitespace ---

    def test_empty_string(self) -> None:
        with pytest.raises(ValueError):
            _validate_select_only("")

    def test_whitespace_only(self) -> None:
        with pytest.raises(ValueError):
            _validate_select_only("   ")

    # --- Edge cases ---

    def test_select_into_blocked(self) -> None:
        """SELECT INTO creates a new table — must be blocked."""
        with pytest.raises(ValueError, match="SELECT INTO"):
            _validate_select_only("SELECT * INTO new_table FROM players")

    def test_explain_select(self) -> None:
        """EXPLAIN should not be allowed — only pure SELECT."""
        with pytest.raises(ValueError):
            _validate_select_only("EXPLAIN SELECT * FROM players")

    # --- Blocked: dangerous functions ---

    def test_pg_sleep_blocked(self) -> None:
        with pytest.raises(ValueError, match="PG_SLEEP"):
            _validate_select_only("SELECT pg_sleep(300)")

    def test_dblink_blocked(self) -> None:
        with pytest.raises(ValueError, match="DBLINK"):
            _validate_select_only("SELECT * FROM dblink('host=evil', 'SELECT 1')")

    def test_pg_read_file_blocked(self) -> None:
        with pytest.raises(ValueError, match="PG_READ_FILE"):
            _validate_select_only("SELECT pg_read_file('/etc/passwd')")


class TestExecuteSql:
    """Tests for execute_sql() using a mocked AsyncSession.

    execute_sql now runs inside `async with db.begin():` and uses fetchmany().
    The mock must support the async context manager protocol on begin().
    """

    def _make_mock_session(
        self, columns: list[str], rows: list[tuple]
    ) -> MagicMock:
        """Build a mock AsyncSession with begin() async context manager."""
        session = MagicMock()
        data_result = MagicMock()
        data_result.keys.return_value = columns
        data_result.fetchmany.return_value = rows
        timeout_result = MagicMock()
        session.execute = AsyncMock(side_effect=[timeout_result, data_result])

        @asynccontextmanager
        async def fake_begin():
            yield

        session.begin = fake_begin
        return session

    async def test_returns_list_of_dicts(self) -> None:
        session = self._make_mock_session(
            columns=["name", "home_runs"],
            rows=[("Aaron Judge", 62), ("Kyle Schwarber", 46)],
        )
        rows = await execute_sql(session, "SELECT name, home_runs FROM batting_stats")
        assert rows == [
            {"name": "Aaron Judge", "home_runs": 62},
            {"name": "Kyle Schwarber", "home_runs": 46},
        ]

    async def test_returns_empty_list_when_no_rows(self) -> None:
        session = self._make_mock_session(columns=["name"], rows=[])
        rows = await execute_sql(session, "SELECT name FROM players WHERE id = -1")
        assert rows == []

    async def test_raises_value_error_for_non_select(self) -> None:
        session = AsyncMock()
        with pytest.raises(ValueError, match="SELECT"):
            await execute_sql(session, "DELETE FROM players")
        session.execute.assert_not_called()

    async def test_raises_value_error_for_multi_statement(self) -> None:
        session = AsyncMock()
        with pytest.raises(ValueError, match="one SQL statement"):
            await execute_sql(session, "SELECT 1; DROP TABLE players")
        session.execute.assert_not_called()

    async def test_reraises_db_exception(self) -> None:
        """DB error on the actual SELECT should propagate."""
        session = MagicMock()
        timeout_result = MagicMock()
        session.execute = AsyncMock(
            side_effect=[timeout_result, RuntimeError("DB connection lost")]
        )

        @asynccontextmanager
        async def fake_begin():
            yield

        session.begin = fake_begin
        with pytest.raises(RuntimeError, match="DB connection lost"):
            await execute_sql(session, "SELECT * FROM players")

    async def test_statement_timeout_is_set(self) -> None:
        """execute_sql must issue SET LOCAL statement_timeout before the query."""
        session = self._make_mock_session(columns=["id"], rows=[(1,)])
        await execute_sql(session, "SELECT id FROM players")
        first_call_arg = session.execute.call_args_list[0].args[0]
        assert "statement_timeout" in str(first_call_arg)
        assert "5000" in str(first_call_arg)

    async def test_single_column_single_row(self) -> None:
        session = self._make_mock_session(columns=["count"], rows=[(42,)])
        rows = await execute_sql(session, "SELECT COUNT(*) AS count FROM players")
        assert rows == [{"count": 42}]


class TestGenerateAnswer:
    """Tests for generate_answer() — both fallback and LLM-wired paths."""

    async def test_returns_no_results_message_for_empty_rows(self) -> None:
        answer = await generate_answer("Who led in home runs?", "SELECT ...", [])
        assert "No results" in answer

    async def test_falls_back_to_str_rows_when_no_api_key(self) -> None:
        """Without an API key the function should return str(rows)."""
        rows = [{"era": 1.92}]
        with patch("app.text_to_sql.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""
            answer = await generate_answer("Best ERA?", "SELECT ...", rows)
        assert "1.92" in answer

    async def test_calls_llm_and_returns_natural_language_answer(self) -> None:
        rows = [{"name": "Aaron Judge", "home_runs": 62}]
        fake_answer = "Aaron Judge led the league with 62 home runs."

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=fake_answer)]

        with patch("app.text_to_sql.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            with patch("app.text_to_sql.anthropic.AsyncAnthropic") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.messages.create = AsyncMock(return_value=mock_message)
                mock_client_cls.return_value = mock_client

                answer = await generate_answer(
                    "Who led in home runs?", "SELECT ...", rows
                )

        assert answer == fake_answer

    async def test_truncates_large_result_sets_to_20_rows(self) -> None:
        """Only the first 20 rows should be sent to the LLM."""
        rows = [{"id": i} for i in range(25)]
        fake_answer = "Lots of players."

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=fake_answer)]

        with patch("app.text_to_sql.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            with patch("app.text_to_sql.anthropic.AsyncAnthropic") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.messages.create = AsyncMock(return_value=mock_message)
                mock_client_cls.return_value = mock_client

                await generate_answer("List players", "SELECT ...", rows)

        # Verify the user message content included "5 more rows" truncation note
        call_kwargs = mock_client.messages.create.call_args.kwargs
        user_msg = call_kwargs["messages"][0]["content"]
        assert "5 more rows" in user_msg

    async def test_falls_back_gracefully_when_llm_returns_empty_content(self) -> None:
        rows = [{"name": "Test"}]
        mock_message = MagicMock()
        mock_message.content = []

        with patch("app.text_to_sql.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            with patch("app.text_to_sql.anthropic.AsyncAnthropic") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.messages.create = AsyncMock(return_value=mock_message)
                mock_client_cls.return_value = mock_client

                answer = await generate_answer("Who?", "SELECT ...", rows)

        # Should fall back to str(rows)
        assert isinstance(answer, str)
        assert len(answer) > 0


class TestStripSqlFence:
    """Tests for the markdown fence stripping helper."""

    def test_strips_sql_fence(self) -> None:
        assert _strip_sql_fence("```sql\nSELECT 1\n```") == "SELECT 1"

    def test_strips_plain_fence(self) -> None:
        assert _strip_sql_fence("```\nSELECT 1\n```") == "SELECT 1"

    def test_no_fence_unchanged(self) -> None:
        assert _strip_sql_fence("SELECT * FROM players") == "SELECT * FROM players"

    def test_strips_surrounding_whitespace(self) -> None:
        assert _strip_sql_fence("  SELECT 1  ") == "SELECT 1"


class TestGenerateSql:
    """Tests for generate_sql() Anthropic wiring."""

    async def test_raises_not_implemented_when_api_key_missing(self) -> None:
        with patch("app.text_to_sql.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""
            with pytest.raises(NotImplementedError, match="not yet configured"):
                await generate_sql("Who hit the most home runs?")

    async def test_returns_sql_from_llm_response(self) -> None:
        fake_sql = "SELECT * FROM batting_stats ORDER BY home_runs DESC LIMIT 1"

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=fake_sql)]

        with patch("app.text_to_sql.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            with patch("app.text_to_sql.anthropic.AsyncAnthropic") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.messages.create = AsyncMock(return_value=mock_message)
                mock_client_cls.return_value = mock_client

                result = await generate_sql("Who hit the most home runs?")

        assert result == fake_sql

    async def test_strips_markdown_fence_from_response(self) -> None:
        wrapped_sql = "```sql\nSELECT * FROM players\n```"
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=wrapped_sql)]

        with patch("app.text_to_sql.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            with patch("app.text_to_sql.anthropic.AsyncAnthropic") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.messages.create = AsyncMock(return_value=mock_message)
                mock_client_cls.return_value = mock_client

                result = await generate_sql("List all players")

        assert result == "SELECT * FROM players"

    async def test_raises_value_error_on_empty_llm_response(self) -> None:
        mock_message = MagicMock()
        mock_message.content = []

        with patch("app.text_to_sql.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            with patch("app.text_to_sql.anthropic.AsyncAnthropic") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.messages.create = AsyncMock(return_value=mock_message)
                mock_client_cls.return_value = mock_client

                with pytest.raises(ValueError, match="empty SQL response"):
                    await generate_sql("empty question?")
