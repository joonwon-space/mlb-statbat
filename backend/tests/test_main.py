"""Endpoint tests for FastAPI app (GET /health, POST /api/query).

The database dependency is mocked via conftest.py so no live DB is needed.
"""

from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for GET /health."""

    async def test_health_returns_ok(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestQueryEndpoint:
    """Tests for POST /api/query."""

    async def test_query_returns_501_when_llm_not_configured(
        self, async_client: AsyncClient
    ) -> None:
        """Stub generate_sql raises NotImplementedError -> 501."""
        response = await async_client.post(
            "/api/query", json={"question": "Who hit the most home runs in 2023?"}
        )
        assert response.status_code == 501
        assert "not yet configured" in response.json()["detail"]

    async def test_query_returns_400_for_empty_question(
        self, async_client: AsyncClient
    ) -> None:
        """Pydantic min_length=3 rejects empty string."""
        response = await async_client.post("/api/query", json={"question": ""})
        assert response.status_code == 422

    async def test_query_returns_422_for_question_too_short(
        self, async_client: AsyncClient
    ) -> None:
        """Pydantic min_length=3 rejects 2-char questions."""
        response = await async_client.post("/api/query", json={"question": "ab"})
        assert response.status_code == 422

    async def test_query_returns_422_for_question_too_long(
        self, async_client: AsyncClient
    ) -> None:
        """Pydantic max_length=500 rejects questions > 500 chars."""
        response = await async_client.post(
            "/api/query", json={"question": "x" * 501}
        )
        assert response.status_code == 422

    async def test_query_returns_422_for_missing_question_field(
        self, async_client: AsyncClient
    ) -> None:
        """Missing required field yields 422."""
        response = await async_client.post("/api/query", json={})
        assert response.status_code == 422

    async def test_query_success_path(self, async_client: AsyncClient) -> None:
        """When generate_sql and execute_sql succeed, returns 200 with full response."""
        fake_sql = "SELECT * FROM batting_stats LIMIT 1"
        fake_rows = [{"player_mlb_id": 1, "home_runs": 40}]
        fake_answer = "The player hit 40 home runs."

        with (
            patch(
                "app.main.generate_sql",
                new=AsyncMock(return_value=fake_sql),
            ),
            patch(
                "app.main.execute_sql",
                new=AsyncMock(return_value=fake_rows),
            ),
            patch(
                "app.main.generate_answer",
                new=AsyncMock(return_value=fake_answer),
            ),
        ):
            response = await async_client.post(
                "/api/query", json={"question": "Who hit the most home runs?"}
            )

        assert response.status_code == 200
        body = response.json()
        assert body["question"] == "Who hit the most home runs?"
        assert body["sql"] == fake_sql
        assert body["result"] == fake_rows
        assert body["answer"] == fake_answer

    async def test_query_returns_400_for_invalid_sql(
        self, async_client: AsyncClient
    ) -> None:
        """execute_sql raises ValueError (SQL guard) -> 400."""
        with (
            patch(
                "app.main.generate_sql",
                new=AsyncMock(return_value="DROP TABLE players"),
            ),
            patch(
                "app.main.execute_sql",
                side_effect=ValueError("Only SELECT queries are permitted"),
            ),
        ):
            response = await async_client.post(
                "/api/query", json={"question": "Drop the players table"}
            )

        assert response.status_code == 400
        assert "SELECT" in response.json()["detail"]

    async def test_query_returns_500_for_db_error(
        self, async_client: AsyncClient
    ) -> None:
        """Unexpected DB error -> 500 with safe message."""
        with (
            patch(
                "app.main.generate_sql",
                new=AsyncMock(return_value="SELECT * FROM batting_stats"),
            ),
            patch(
                "app.main.execute_sql",
                side_effect=RuntimeError("connection lost"),
            ),
        ):
            response = await async_client.post(
                "/api/query", json={"question": "Show me batting stats"}
            )

        assert response.status_code == 500
        detail = response.json()["detail"]
        # Must not leak raw exception message
        assert "connection lost" not in detail
        assert "rephrasing" in detail

    async def test_rate_limit_handler_registered(self) -> None:
        """The 429 error handler must be registered on the app."""
        from slowapi.errors import RateLimitExceeded
        from app.main import app as fastapi_app

        assert RateLimitExceeded in fastapi_app.exception_handlers

    async def test_rate_limiter_attached_to_app_state(self) -> None:
        """The limiter must be attached to app.state so slowapi middleware works."""
        from app.main import app as fastapi_app, limiter

        assert fastapi_app.state.limiter is limiter
