"""Tests for the synchronous Wordmade ID client."""

from __future__ import annotations

import httpx
import pytest

from wordmade_id import (
    NotFoundError,
    ProfileUpdate,
    RateLimitedError,
    RegisterRequest,
    TokenRequest,
    UnauthorizedError,
    WordmadeID,
)
from wordmade_id.errors import ForbiddenError

from .conftest import error_response, json_response, make_sync_client


class TestLookup:
    def test_lookup_by_handle(self, mock_agent_data: dict) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert "/v1/agents/@@testbot" in str(request.url)
            return json_response(mock_agent_data)

        client = make_sync_client(handler)
        agent = client.lookup("@@testbot")
        assert agent.uuid == "550e8400-e29b-41d4-a716-446655440000"
        assert agent.handle == "@@testbot"
        assert agent.name == "Test Bot"
        assert "code-review" in agent.capabilities

    def test_lookup_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return error_response(404, "agent_not_found", "No agent found")

        client = make_sync_client(handler)
        with pytest.raises(NotFoundError) as exc:
            client.lookup("@@nonexistent")
        assert exc.value.status_code == 404
        assert exc.value.code == "agent_not_found"


class TestSearch:
    def test_search_with_filters(self) -> None:
        page_data = {
            "agents": [{"handle": "@@bot1"}],
            "total": 42,
            "page": 1,
            "per_page": 20,
            "pages": 3,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert "skill=code-review" in str(request.url)
            assert "min_trust=70" in str(request.url)
            return json_response(page_data)

        client = make_sync_client(handler)
        from wordmade_id import SearchParams

        page = client.search(SearchParams(skill="code-review", min_trust=70))
        assert page.total == 42
        assert page.pages == 3
        assert len(page.agents) == 1


class TestVerify:
    def test_verify_valid_token(self) -> None:
        verify_data = {
            "valid": True,
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "handle": "@@testbot",
            "trust_score": 85,
            "cert_level": 2,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "/v1/verify" in str(request.url)
            assert request.headers.get("Authorization") == "Bearer isk_test"
            return json_response(verify_data)

        client = make_sync_client(handler, service_key="isk_test")
        result = client.verify("eyJ.test.token", "my-service")
        assert result.valid is True
        assert result.trust_score == 85
        assert result.cert_level == 2

    def test_verify_invalid_token(self) -> None:
        verify_data = {"valid": False, "error": "expired"}

        def handler(request: httpx.Request) -> httpx.Response:
            return json_response(verify_data)

        client = make_sync_client(handler)
        result = client.verify("expired.token")
        assert result.valid is False
        assert result.error == "expired"


class TestRegister:
    def test_register_success(self) -> None:
        reg_data = {
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "handle": "@@newbot",
            "api_key": "iak_secretkey",
            "api_key_id": "key_123",
            "profile_url": "https://id.wordmade.world/agents/550e8400",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "/v1/agents/register" in str(request.url)
            return json_response(reg_data, status_code=201)

        client = make_sync_client(handler)
        resp = client.register(
            RegisterRequest(
                cert_token="wmn_test_token",
                handle="newbot",
                name="New Bot",
                accepted_terms=True,
            )
        )
        assert resp.uuid == "550e8400-e29b-41d4-a716-446655440000"
        assert resp.api_key == "iak_secretkey"
        assert resp.api_key_id == "key_123"


class TestIssueToken:
    def test_issue_token_success(self) -> None:
        token_data = {
            "token": "eyJ.new.token",
            "expires_at": "2026-03-05T00:00:00Z",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            return json_response(token_data)

        client = make_sync_client(handler)
        resp = client.issue_token(
            TokenRequest(
                api_key="iak_key",
                cert_token="wmn_test",
                uuid="550e8400-e29b-41d4-a716-446655440000",
            )
        )
        assert resp.token == "eyJ.new.token"


class TestUpdateProfile:
    def test_update_name(self, mock_agent_data: dict) -> None:
        updated = {**mock_agent_data, "name": "Updated Name"}

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "PUT"
            assert request.headers.get("Authorization") == "Bearer iak_agentkey"
            return json_response(updated)

        client = make_sync_client(handler, agent_key="iak_agentkey")
        agent = client.update_profile(
            "550e8400-e29b-41d4-a716-446655440000",
            ProfileUpdate(name="Updated Name"),
        )
        assert agent.name == "Updated Name"


class TestGetStats:
    def test_get_stats(self) -> None:
        stats_data = {
            "total_agents": 1000,
            "certified_today": 42,
            "capabilities": {"code-review": 150},
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert "/v1/directory/stats" in str(request.url)
            return json_response(stats_data)

        client = make_sync_client(handler)
        stats = client.get_stats()
        assert stats.total_agents == 1000
        assert stats.certified_today == 42


class TestErrors:
    def test_rate_limited(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return error_response(429, "rate_limited", "Too many requests")

        client = make_sync_client(handler)
        with pytest.raises(RateLimitedError):
            client.lookup("@@someone")

    def test_unauthorized(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return error_response(401, "invalid_key", "Invalid API key")

        client = make_sync_client(handler)
        with pytest.raises(UnauthorizedError):
            client.verify("token")

    def test_forbidden(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return error_response(403, "not_owner", "Not the agent owner")

        client = make_sync_client(handler)
        with pytest.raises(ForbiddenError):
            client.update_profile("uuid", ProfileUpdate(name="hacked"))


class TestContextManager:
    def test_sync_context_manager(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response({"total_agents": 0, "certified_today": 0, "capabilities": {}})

        with make_sync_client(handler) as client:
            stats = client.get_stats()
            assert stats.total_agents == 0
