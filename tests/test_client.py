"""Tests for the synchronous Wordmade ID client."""

from __future__ import annotations

import httpx
import pytest

from wordmade_id import (
    NotFoundError,
    ProfileUpdate,
    RateLimitedError,
    RecoverConfirmRequest,
    RecoverRequest,
    RegisterRequest,
    RegistryParams,
    Skill,
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


# ------------------------------------------------------------------
# Skills
# ------------------------------------------------------------------


class TestListSkills:
    def test_list_skills(self) -> None:
        data = {
            "skills": [{"id": "code-review", "name": "Code Review", "tags": ["go"]}],
            "count": 1,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert "/v1/agents/uuid1/skills" in str(request.url)
            return json_response(data)

        client = make_sync_client(handler)
        result = client.list_skills("uuid1")
        assert result.count == 1
        assert result.skills[0].id == "code-review"


class TestAddSkill:
    def test_add_skill(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.headers.get("Authorization") == "Bearer iak_key"
            return json_response(
                {"id": "testing", "name": "Testing"}, status_code=201
            )

        client = make_sync_client(handler, agent_key="iak_key")
        result = client.add_skill("uuid1", Skill(id="testing", name="Testing"))
        assert result.id == "testing"


class TestDeleteSkill:
    def test_delete_skill(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            assert "/skills/code-review" in str(request.url)
            return json_response({})

        client = make_sync_client(handler, agent_key="iak_key")
        client.delete_skill("uuid1", "code-review")


# ------------------------------------------------------------------
# Custom Fields
# ------------------------------------------------------------------


class TestListCustomFields:
    def test_list_custom_fields(self) -> None:
        data = {
            "fields": [{"key": "website", "value": "https://example.com", "well_known": True}],
            "count": 1,
            "quota": 5,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert "/v1/agents/uuid1/custom" in str(request.url)
            return json_response(data)

        client = make_sync_client(handler, agent_key="iak_key")
        result = client.list_custom_fields("uuid1")
        assert result.quota == 5
        assert result.fields[0].key == "website"


class TestSetCustomField:
    def test_set_custom_field(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "PUT"
            return json_response({"key": "website", "value": "https://example.com"}, status_code=201)

        client = make_sync_client(handler, agent_key="iak_key")
        client.set_custom_field("uuid1", "website", "https://example.com")


class TestListWellKnownFields:
    def test_list_well_known_fields(self) -> None:
        data = {
            "fields": [{"key": "website", "description": "URL", "category": "contact", "rendering": "link"}],
            "count": 1,
            "note": "Recognized keys",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert "/v1/custom-fields" in str(request.url)
            return json_response(data)

        client = make_sync_client(handler)
        result = client.list_well_known_fields()
        assert result.count == 1


# ------------------------------------------------------------------
# Private Metadata
# ------------------------------------------------------------------


class TestListPrivateMetadata:
    def test_list_private_metadata(self) -> None:
        data = {
            "keys": [{"key": "model", "value": "claude-3.5"}],
            "count": 1,
            "quota": 5,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert "/v1/agents/uuid1/private" in str(request.url)
            return json_response(data)

        client = make_sync_client(handler, agent_key="iak_key")
        result = client.list_private_metadata("uuid1")
        assert result.keys[0].key == "model"


class TestGetPrivateMetadata:
    def test_get_private_metadata(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert "/private/model" in str(request.url)
            return json_response({"key": "model", "value": "claude-3.5"})

        client = make_sync_client(handler, agent_key="iak_key")
        result = client.get_private_metadata("uuid1", "model")
        assert result.value == "claude-3.5"


class TestSetPrivateMetadata:
    def test_set_private_metadata(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "PUT"
            return json_response({"key": "model"})

        client = make_sync_client(handler, agent_key="iak_key")
        client.set_private_metadata("uuid1", "model", "claude-3.5")


# ------------------------------------------------------------------
# Sessions
# ------------------------------------------------------------------


class TestCreateSession:
    def test_create_session(self) -> None:
        data = {
            "token": "ias_testsession",
            "expires_at": "2026-03-06T12:30:00Z",
            "agent_uuid": "uuid1",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.headers.get("Authorization") == "Bearer iak_key"
            return json_response(data, status_code=201)

        client = make_sync_client(handler, agent_key="iak_key")
        result = client.create_session()
        assert result.token == "ias_testsession"


class TestRevokeSession:
    def test_revoke_session(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            return json_response({"message": "session revoked"})

        client = make_sync_client(handler, agent_key="ias_session")
        client.revoke_session()


# ------------------------------------------------------------------
# Key Rotation
# ------------------------------------------------------------------


class TestRotateKey:
    def test_rotate_key(self) -> None:
        data = {
            "api_key": "iak_newkey",
            "api_key_id": "key_456",
            "message": "new key generated",
            "revoked_keys": 1,
            "profile_url": "/v1/agents/uuid1",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "/keys/rotate" in str(request.url)
            return json_response(data, status_code=201)

        client = make_sync_client(handler, agent_key="iak_key")
        result = client.rotate_key("uuid1")
        assert result.api_key == "iak_newkey"
        assert result.revoked_keys == 1


# ------------------------------------------------------------------
# Recovery
# ------------------------------------------------------------------


class TestRecover:
    def test_recover(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "/v1/agents/recover" in str(request.url)
            return json_response({"message": "recovery email sent"})

        client = make_sync_client(handler)
        client.recover(RecoverRequest(cert_token="wmn_test", handle="testbot"))


class TestRecoverConfirm:
    def test_recover_confirm(self) -> None:
        data = {
            "uuid": "uuid1",
            "handle": "testbot",
            "api_key": "iak_newkey",
            "api_key_id": "key_789",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert "/recover/confirm" in str(request.url)
            return json_response(data)

        client = make_sync_client(handler)
        result = client.recover_confirm(
            RecoverConfirmRequest(recovery_token="abc123", cert_token="wmn_test")
        )
        assert result.api_key == "iak_newkey"


# ------------------------------------------------------------------
# Registry
# ------------------------------------------------------------------


class TestGetRegistry:
    def test_get_registry(self) -> None:
        data = {
            "cards": [{"handle": "@@bot1"}],
            "total": 10,
            "page": 1,
            "per_page": 20,
            "pages": 1,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert "/v1/registry" in str(request.url)
            assert "min_trust=70" in str(request.url)
            return json_response(data)

        client = make_sync_client(handler)
        result = client.get_registry(RegistryParams(min_trust=70))
        assert result.total == 10
