"""Shared pytest fixtures for the MLB StatBat backend test suite."""

import os
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

# Set required env var before importing app (config.py requires DATABASE_URL)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.main import app  # noqa: E402
from app.database import get_db  # noqa: E402


@pytest.fixture
async def async_client() -> AsyncClient:
    """Async HTTP client wired to the FastAPI app via ASGI transport.

    The database dependency is overridden with a mock so no live DB is needed.
    """
    mock_db = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_db() -> AsyncMock:
    """Return a mocked AsyncSession for unit tests that call execute_sql directly."""
    session = AsyncMock()
    result = MagicMock()
    result.keys.return_value = []
    result.fetchall.return_value = []
    session.execute.return_value = result
    return session
