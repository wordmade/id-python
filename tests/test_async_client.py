"""Tests for the asynchronous Wordmade ID client."""

from __future__ import annotations

import httpx
import pytest

from wordmade_id import (
    NotFoundError,
    ProfileUpdate,
    RateLimitedError,
    RegisterRequest,
    SearchParams,
    TokenRequest,
)

from .conftest import error_response, json_response, make_async_client


class TestAsyncLookup:
    @pytest.mark.asyncio
    async def test_lookup_by_handle(self, mock_agent_data: dict) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            return json_response(mock_agent_data)

        client = make_async_client(handler)
        agent = await client.lookup("@@testbot")
        assert agent.uuid == "550e8400-e29b-41d4-a716-446655440000"
        assert agent.handle == "@@testbot"
        await client.close()

    @pytest.mark.asyncio
    async def test_lookup_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return error_response(404, "agent_not_found", "Not found")

        client = make_async_client(handler)
        with pytest.raises(NotFoundError):
            await client.lookup("@@gone")
        await client.close()


class TestAsyncSearch:
    @pytest.mark.asyncio
    async def test_search(self) -> None:
        page_data = {
            "agents": [{"handle": "@@bot1"}],
            "total": 10,
            "page": 1,
            "per_page": 20,
            "pages": 1,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return json_response(page_data)

        client = make_async_client(handler)
        page = await client.search(SearchParams(skill="testing"))
        assert page.total == 10
        await client.close()


class TestAsyncVerify:
    @pytest.mark.asyncio
    async def test_verify(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers.get("Authorization") == "Bearer isk_key"
            return json_response({"valid": True, "handle": "@@bot", "trust_score": 90})

        client = make_async_client(handler, service_key="isk_key")
        result = await client.verify("eyJ.token", "aud")
        assert result.valid is True
        assert result.trust_score == 90
        await client.close()


class TestAsyncRegister:
    @pytest.mark.asyncio
    async def test_register(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response(
                {
                    "uuid": "uuid-123",
                    "handle": "@@new",
                    "api_key": "iak_key",
                    "api_key_id": "kid",
                    "profile_url": "https://id.wordmade.world/agents/uuid-123",
                },
                status_code=201,
            )

        client = make_async_client(handler)
        resp = await client.register(
            RegisterRequest(
                cert_token="wmn_test",
                handle="new",
                name="New",
                accepted_terms=True,
            )
        )
        assert resp.api_key == "iak_key"
        await client.close()


class TestAsyncIssueToken:
    @pytest.mark.asyncio
    async def test_issue_token(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response({"token": "eyJ.t", "expires_at": "2026-03-05T00:00:00Z"})

        client = make_async_client(handler)
        resp = await client.issue_token(
            TokenRequest(api_key="iak_k", cert_token="wmn_t", uuid="uuid")
        )
        assert resp.token == "eyJ.t"
        await client.close()


class TestAsyncUpdateProfile:
    @pytest.mark.asyncio
    async def test_update(self, mock_agent_data: dict) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers.get("Authorization") == "Bearer iak_key"
            return json_response({**mock_agent_data, "name": "New Name"})

        client = make_async_client(handler, agent_key="iak_key")
        agent = await client.update_profile("uuid", ProfileUpdate(name="New Name"))
        assert agent.name == "New Name"
        await client.close()


class TestAsyncErrors:
    @pytest.mark.asyncio
    async def test_rate_limited(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return error_response(429, "rate_limited", "Slow down")

        client = make_async_client(handler)
        with pytest.raises(RateLimitedError):
            await client.lookup("@@someone")
        await client.close()


class TestAsyncContextManager:
    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response({"total_agents": 0, "certified_today": 0, "capabilities": {}})

        async with make_async_client(handler) as client:
            stats = await client.get_stats()
            assert stats.total_agents == 0
