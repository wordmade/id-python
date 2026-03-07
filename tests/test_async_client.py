"""Tests for the asynchronous Wordmade ID client."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from wordmade_id import (
    NotFoundError,
    ProfileUpdate,
    RateLimitedError,
    RegisterRequest,
    SearchParams,
    TokenRequest,
    UnauthorizedError,
)

from .conftest import error_response, json_response, make_async_client

if TYPE_CHECKING:
    import httpx


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


class TestAsyncGetStats:
    @pytest.mark.asyncio
    async def test_get_stats(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response(
                {"total_agents": 500, "certified_today": 10, "capabilities": {"testing": 50}}
            )

        async with make_async_client(handler) as client:
            stats = await client.get_stats()
            assert stats.total_agents == 500
            assert stats.capabilities["testing"] == 50


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


# ------------------------------------------------------------------
# OAuth 2.0
# ------------------------------------------------------------------


class TestAsyncOAuthClientCredentials:
    @pytest.mark.asyncio
    async def test_client_credentials(self) -> None:
        token_data = {
            "access_token": "eyJ.oauth.token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "profile cert",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "/v1/oauth/token" in str(request.url)
            ct = request.headers.get("content-type", "")
            assert "application/x-www-form-urlencoded" in ct
            body = request.content.decode()
            assert "grant_type=client_credentials" in body
            assert "client_id=wid_testclient" in body
            return json_response(token_data)

        async with make_async_client(handler) as client:
            result = await client.oauth_client_credentials(
                "wid_testclient", "secret123", "profile cert"
            )
            assert result.access_token == "eyJ.oauth.token"
            assert result.token_type == "Bearer"
            assert result.expires_in == 3600

    @pytest.mark.asyncio
    async def test_client_credentials_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return error_response(401, "invalid_client", "Invalid client credentials")

        async with make_async_client(handler) as client:
            with pytest.raises(UnauthorizedError):
                await client.oauth_client_credentials("bad_id", "bad_secret")


class TestAsyncOAuthBuildAuthorizeURL:
    @pytest.mark.asyncio
    async def test_build_authorize_url(self) -> None:
        client = make_async_client(lambda r: json_response({}))
        result = client.oauth_build_authorize_url(
            "wid_abc", "https://app.example.com/callback", "profile", "xyzstate"
        )

        assert "/v1/oauth/authorize?" in result.url
        assert "response_type=code" in result.url
        assert "client_id=wid_abc" in result.url
        assert "state=xyzstate" in result.url
        assert "code_challenge_method=S256" in result.url
        assert result.code_verifier != ""

        # Verify PKCE: sha256(verifier) == code_challenge
        import base64
        import hashlib
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(result.url)
        qs = parse_qs(parsed.query)
        challenge_in_url = qs["code_challenge"][0]
        expected = (
            base64.urlsafe_b64encode(
                hashlib.sha256(result.code_verifier.encode()).digest()
            )
            .rstrip(b"=")
            .decode()
        )
        assert challenge_in_url == expected
        await client.close()


class TestAsyncOAuthExchangeCode:
    @pytest.mark.asyncio
    async def test_exchange_code(self) -> None:
        token_data = {
            "access_token": "eyJ.access",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "profile",
            "refresh_token": "rt_abc123",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            body = request.content.decode()
            assert "grant_type=authorization_code" in body
            assert "code=authcode123" in body
            assert "code_verifier=myverifier" in body
            return json_response(token_data)

        async with make_async_client(handler) as client:
            result = await client.oauth_exchange_code(
                "wid_abc",
                "secret",
                "authcode123",
                "https://app.example.com/callback",
                "myverifier",
            )
            assert result.refresh_token == "rt_abc123"


class TestAsyncOAuthRefreshToken:
    @pytest.mark.asyncio
    async def test_refresh_token(self) -> None:
        token_data = {
            "access_token": "eyJ.new.access",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "profile",
            "refresh_token": "rt_new456",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            body = request.content.decode()
            assert "grant_type=refresh_token" in body
            assert "refresh_token=rt_old123" in body
            return json_response(token_data)

        async with make_async_client(handler) as client:
            result = await client.oauth_refresh_token("wid_abc", "secret", "rt_old123")
            assert result.access_token == "eyJ.new.access"
            assert result.refresh_token == "rt_new456"


class TestAsyncOAuthUserInfo:
    @pytest.mark.asyncio
    async def test_userinfo(self) -> None:
        info_data = {
            "sub": "550e8400-e29b-41d4-a716-446655440000",
            "wm_handle": "@@testbot",
            "wm_name": "Test Bot",
            "wm_cert_level": 2,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert "/v1/oauth/userinfo" in str(request.url)
            assert request.headers.get("Authorization") == "Bearer eyJ.access.token"
            return json_response(info_data)

        async with make_async_client(handler) as client:
            result = await client.oauth_userinfo("eyJ.access.token")
            assert result.sub == "550e8400-e29b-41d4-a716-446655440000"
            assert result.wm_handle == "@@testbot"
            assert result.wm_cert_level == 2


class TestAsyncOAuthRevoke:
    @pytest.mark.asyncio
    async def test_revoke(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "/v1/oauth/revoke" in str(request.url)
            body = request.content.decode()
            assert "token=rt_revokeme" in body
            assert "token_type_hint=refresh_token" in body
            return json_response({})

        async with make_async_client(handler) as client:
            await client.oauth_revoke(
                "wid_abc", "secret", "rt_revokeme", "refresh_token"
            )


class TestAsyncOAuthDiscovery:
    @pytest.mark.asyncio
    async def test_discovery(self) -> None:
        discovery_data = {
            "issuer": "https://id.wordmade.world",
            "authorization_endpoint": "https://id.wordmade.world/v1/oauth/authorize",
            "token_endpoint": "https://id.wordmade.world/v1/oauth/token",
            "userinfo_endpoint": "https://id.wordmade.world/v1/oauth/userinfo",
            "revocation_endpoint": "https://id.wordmade.world/v1/oauth/revoke",
            "jwks_uri": "https://id.wordmade.world/.well-known/jwks.json",
            "scopes_supported": ["profile", "cert", "email"],
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert "/.well-known/openid-configuration" in str(request.url)
            return json_response(discovery_data)

        async with make_async_client(handler) as client:
            result = await client.oauth_discovery()
            assert result.issuer == "https://id.wordmade.world"
            assert len(result.scopes_supported) == 3
