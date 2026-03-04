"""Shared test fixtures for the Wordmade ID Python SDK."""

from __future__ import annotations

from typing import Any, Dict

import httpx
import pytest

from wordmade_id import AsyncWordmadeID, WordmadeID


class MockTransport(httpx.BaseTransport):
    """Mock transport that returns predefined responses."""

    def __init__(self, handler: Any) -> None:
        self._handler = handler

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return self._handler(request)


class MockAsyncTransport(httpx.AsyncBaseTransport):
    """Mock async transport that returns predefined responses."""

    def __init__(self, handler: Any) -> None:
        self._handler = handler

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return self._handler(request)


def json_response(data: Dict[str, Any], status_code: int = 200) -> httpx.Response:
    """Create a mock JSON response."""
    return httpx.Response(status_code=status_code, json=data)


def error_response(status_code: int, code: str, message: str) -> httpx.Response:
    """Create a mock error response."""
    return httpx.Response(
        status_code=status_code,
        json={"error": code, "message": message},
    )


@pytest.fixture
def mock_agent_data() -> Dict[str, Any]:
    return {
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "handle": "@@testbot",
        "name": "Test Bot",
        "bio_oneliner": "A test agent",
        "bio": "Long bio here",
        "avatar_url": "",
        "country": "US",
        "city": "San Francisco",
        "business": "",
        "capabilities": ["code-review", "testing"],
        "verification": {"level": "certified", "trust_score": 85},
        "custom": {"framework": "langchain"},
        "world_presences": [],
        "stats": {"verifications": 42},
    }


def make_sync_client(handler: Any, **kwargs: Any) -> WordmadeID:
    """Create a sync client with a mock transport."""
    transport = MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    return WordmadeID(
        base_url="https://test.api",
        http_client=http_client,
        **kwargs,
    )


def make_async_client(handler: Any, **kwargs: Any) -> AsyncWordmadeID:
    """Create an async client with a mock transport."""
    transport = MockAsyncTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    return AsyncWordmadeID(
        base_url="https://test.api",
        http_client=http_client,
        **kwargs,
    )
