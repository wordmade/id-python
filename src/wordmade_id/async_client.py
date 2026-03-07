"""Asynchronous client for the Wordmade ID API."""

from __future__ import annotations

from urllib.parse import quote, urlencode

import httpx

from .constants import DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from .errors import classify_error
from .client import _generate_pkce
from .types import (
    Agent,
    AvatarResponse,
    CustomFieldsResponse,
    DirectoryPage,
    DirectoryStats,
    MetadataEntry,
    MetadataListResponse,
    OAuthAuthorizeResult,
    OAuthDiscoveryResponse,
    OAuthTokenResponse,
    OAuthUserInfoResponse,
    ProfileUpdate,
    RecoverConfirmRequest,
    RecoverConfirmResponse,
    RecoverRequest,
    RegisterRequest,
    RegisterResponse,
    RegistryPage,
    RegistryParams,
    RotateKeyResponse,
    SearchParams,
    SessionResponse,
    Skill,
    SkillsResponse,
    TokenRequest,
    TokenResponse,
    VerifyResult,
    WellKnownFieldsResponse,
)


class AsyncWordmadeID:
    """Asynchronous client for the Wordmade ID agent identity API.

    Args:
        base_url: API base URL (default: https://api.id.wordmade.world).
        service_key: isk_ service key for verification calls.
        agent_key: iak_ or ias_ agent key for authenticated agent operations.
        timeout: HTTP request timeout in seconds.
        http_client: Custom httpx.AsyncClient instance.
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        service_key: str = "",
        agent_key: str = "",
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_key = service_key
        self._agent_key = agent_key
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close the underlying HTTP client (only if we own it)."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncWordmadeID:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: object | None = None,
        params: dict[str, str] | None = None,
        auth_key: str = "",
    ) -> dict:  # type: ignore[type-arg]
        headers: dict[str, str] = {"Accept": "application/json"}
        if auth_key:
            headers["Authorization"] = f"Bearer {auth_key}"

        resp = await self._client.request(
            method,
            f"{self._base_url}{path}",
            json=json_body,
            params=params,
            headers=headers,
        )

        if resp.status_code >= 400:
            try:
                data = resp.json()
                code = data.get("error", "unknown")
                message = data.get("message", data.get("error_description", resp.text))
            except Exception:
                code = "unknown"
                message = resp.text
            raise classify_error(resp.status_code, code, message)

        if not resp.content:
            return {}
        return resp.json()  # type: ignore[no-any-return]

    # ------------------------------------------------------------------
    # Read-only (no auth required)
    # ------------------------------------------------------------------

    async def lookup(self, identifier: str) -> Agent:
        """Fetch a public agent profile by UUID or @@handle."""
        path = f"/v1/agents/{quote(identifier, safe='@')}"
        data = await self._request("GET", path)
        return Agent.from_dict(data)

    async def search(self, params: SearchParams | None = None, **kwargs: object) -> DirectoryPage:
        """Search the agent directory with optional filters."""
        if params is None:
            params = SearchParams(**kwargs)  # type: ignore[arg-type]
        data = await self._request("GET", "/v1/directory", params=params.to_query())
        return DirectoryPage.from_dict(data)

    async def get_stats(self) -> DirectoryStats:
        """Get aggregate directory statistics."""
        data = await self._request("GET", "/v1/directory/stats")
        return DirectoryStats.from_dict(data)

    # ------------------------------------------------------------------
    # Verification (optional isk_ service key)
    # ------------------------------------------------------------------

    async def verify(self, token: str, audience: str = "") -> VerifyResult:
        """Verify an agent's JWT identity token."""
        body: dict[str, str] = {"token": token}
        if audience:
            body["audience"] = audience
        data = await self._request("POST", "/v1/verify", json_body=body, auth_key=self._service_key)
        return VerifyResult.from_dict(data)

    # ------------------------------------------------------------------
    # Agent operations (key in body, not Bearer)
    # ------------------------------------------------------------------

    async def register(self, request: RegisterRequest) -> RegisterResponse:
        """Register a new agent identity.

        The cert_token must contain a valid Wordmade Certification pass (wmn_ prefix).
        """
        data = await self._request("POST", "/v1/agents/register", json_body=request.to_dict())
        return RegisterResponse.from_dict(data)

    async def issue_token(self, request: TokenRequest) -> TokenResponse:
        """Request a JWT identity token for an agent.

        The API key is included in the request body (not as a Bearer header).
        """
        data = await self._request("POST", "/v1/agents/token", json_body=request.to_dict())
        return TokenResponse.from_dict(data)

    # ------------------------------------------------------------------
    # Agent profile (Bearer iak_ or ias_ via agent_key)
    # ------------------------------------------------------------------

    async def update_profile(self, agent_uuid: str, fields: ProfileUpdate) -> Agent:
        """Update an agent's public profile fields.

        Requires agent_key to be set (iak_ or ias_).
        """
        path = f"/v1/agents/{quote(agent_uuid, safe='')}"
        data = await self._request(
            "PUT", path, json_body=fields.to_dict(), auth_key=self._agent_key
        )
        return Agent.from_dict(data)

    # ------------------------------------------------------------------
    # Skills (public read, agent auth write)
    # ------------------------------------------------------------------

    async def list_skills(self, agent_uuid: str) -> SkillsResponse:
        """List all skills for an agent (public, no auth required)."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/skills"
        data = await self._request("GET", path)
        return SkillsResponse.from_dict(data)

    async def add_skill(self, agent_uuid: str, skill: Skill) -> Skill:
        """Add a skill to the agent. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/skills"
        data = await self._request(
            "POST", path, json_body=skill.to_dict(), auth_key=self._agent_key
        )
        return Skill.from_dict(data)

    async def replace_skills(self, agent_uuid: str, skills: list[Skill]) -> SkillsResponse:
        """Replace all skills for the agent. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/skills"
        body = {"skills": [s.to_dict() for s in skills]}
        data = await self._request("PUT", path, json_body=body, auth_key=self._agent_key)
        return SkillsResponse.from_dict(data)

    async def delete_skill(self, agent_uuid: str, skill_id: str) -> None:
        """Remove a skill from the agent. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/skills/{quote(skill_id, safe='')}"
        await self._request("DELETE", path, auth_key=self._agent_key)

    # ------------------------------------------------------------------
    # Custom Fields (agent auth)
    # ------------------------------------------------------------------

    async def list_custom_fields(self, agent_uuid: str) -> CustomFieldsResponse:
        """List all custom fields for the agent. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/custom"
        data = await self._request("GET", path, auth_key=self._agent_key)
        return CustomFieldsResponse.from_dict(data)

    async def set_custom_field(self, agent_uuid: str, key: str, value: str) -> None:
        """Set a custom field on the agent's public profile. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/custom/{quote(key, safe='')}"
        await self._request("PUT", path, json_body={"value": value}, auth_key=self._agent_key)

    async def delete_custom_field(self, agent_uuid: str, key: str) -> None:
        """Remove a custom field. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/custom/{quote(key, safe='')}"
        await self._request("DELETE", path, auth_key=self._agent_key)

    async def list_well_known_fields(self) -> WellKnownFieldsResponse:
        """List recognized custom field keys (public, no auth)."""
        data = await self._request("GET", "/v1/custom-fields")
        return WellKnownFieldsResponse.from_dict(data)

    # ------------------------------------------------------------------
    # Private Metadata (agent auth, AES-256-GCM encrypted at rest)
    # ------------------------------------------------------------------

    async def list_private_metadata(self, agent_uuid: str) -> MetadataListResponse:
        """List all private metadata keys and values. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/private"
        data = await self._request("GET", path, auth_key=self._agent_key)
        return MetadataListResponse.from_dict(data)

    async def get_private_metadata(self, agent_uuid: str, key: str) -> MetadataEntry:
        """Get a single private metadata value. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/private/{quote(key, safe='')}"
        data = await self._request("GET", path, auth_key=self._agent_key)
        return MetadataEntry.from_dict(data)

    async def set_private_metadata(self, agent_uuid: str, key: str, value: str) -> None:
        """Set a private metadata value. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/private/{quote(key, safe='')}"
        await self._request("PUT", path, json_body={"value": value}, auth_key=self._agent_key)

    async def delete_private_metadata(self, agent_uuid: str, key: str) -> None:
        """Remove a private metadata key. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/private/{quote(key, safe='')}"
        await self._request("DELETE", path, auth_key=self._agent_key)

    # ------------------------------------------------------------------
    # Sessions (iak_ only for create, iak_/ias_ for revoke)
    # ------------------------------------------------------------------

    async def create_session(self) -> SessionResponse:
        """Create a short-lived agent session token (ias_, 30 min TTL).

        Requires agent_key set with an iak_ key (session tokens rejected).
        """
        data = await self._request("POST", "/v1/agents/session", auth_key=self._agent_key)
        return SessionResponse.from_dict(data)

    async def revoke_session(self) -> None:
        """Revoke the current session (logout). Requires agent_key."""
        await self._request("DELETE", "/v1/agents/session", auth_key=self._agent_key)

    # ------------------------------------------------------------------
    # Key Rotation (iak_ only)
    # ------------------------------------------------------------------

    async def rotate_key(self, agent_uuid: str) -> RotateKeyResponse:
        """Rotate the agent's API key. Requires agent_key set with iak_.

        The old key is revoked and a new one is returned.
        All active sessions are invalidated.
        """
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/keys/rotate"
        data = await self._request("POST", path, auth_key=self._agent_key)
        return RotateKeyResponse.from_dict(data)

    # ------------------------------------------------------------------
    # Avatar (agent auth for write, public read)
    # ------------------------------------------------------------------

    async def upload_avatar(
        self, agent_uuid: str, image: bytes, content_type: str
    ) -> AvatarResponse:
        """Upload an avatar image. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/avatar"
        headers: dict[str, str] = {"Accept": "application/json"}
        if self._agent_key:
            headers["Authorization"] = f"Bearer {self._agent_key}"
        resp = await self._client.post(
            f"{self._base_url}{path}",
            files={"avatar": ("avatar", image, content_type)},
            headers=headers,
        )
        if resp.status_code >= 400:
            try:
                data = resp.json()
                code = data.get("error", "unknown")
                message = data.get("message", data.get("error_description", resp.text))
            except Exception:
                code = "unknown"
                message = resp.text
            raise classify_error(resp.status_code, code, message)
        return AvatarResponse.from_dict(resp.json())

    async def delete_avatar(self, agent_uuid: str) -> None:
        """Remove the agent's avatar. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/avatar"
        await self._request("DELETE", path, auth_key=self._agent_key)

    # ------------------------------------------------------------------
    # Recovery (no auth — uses cert_token in body)
    # ------------------------------------------------------------------

    async def recover(self, request: RecoverRequest) -> None:
        """Initiate key recovery for an agent. Requires a valid cert_token."""
        await self._request("POST", "/v1/agents/recover", json_body=request.to_dict())

    async def recover_confirm(self, request: RecoverConfirmRequest) -> RecoverConfirmResponse:
        """Complete key recovery with the recovery token from email."""
        data = await self._request(
            "POST", "/v1/agents/recover/confirm", json_body=request.to_dict()
        )
        return RecoverConfirmResponse.from_dict(data)

    # ------------------------------------------------------------------
    # Registry (public, A2A agent card registry)
    # ------------------------------------------------------------------

    async def get_registry(self, params: RegistryParams | None = None) -> RegistryPage:
        """Query the A2A agent card registry with optional filters."""
        query = params.to_query() if params else {}
        data = await self._request("GET", "/v1/registry", params=query or None)
        return RegistryPage.from_dict(data)

    # ------------------------------------------------------------------
    # OAuth 2.0
    # ------------------------------------------------------------------

    async def _form_request(self, path: str, *, data: dict[str, str]) -> dict:  # type: ignore[type-arg]
        """POST a form-encoded request and return the JSON response."""
        headers: dict[str, str] = {"Accept": "application/json"}
        resp = await self._client.post(
            f"{self._base_url}{path}",
            data=data,
            headers=headers,
        )
        if resp.status_code >= 400:
            try:
                body = resp.json()
                code = body.get("error", "unknown")
                message = body.get("message", body.get("error_description", resp.text))
            except Exception:
                code = "unknown"
                message = resp.text
            raise classify_error(resp.status_code, code, message)
        if not resp.content:
            return {}
        return resp.json()  # type: ignore[no-any-return]

    async def oauth_client_credentials(
        self, client_id: str, client_secret: str, scope: str = ""
    ) -> OAuthTokenResponse:
        """Exchange client credentials for an access token (RFC 6749 §4.4)."""
        form: dict[str, str] = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        if scope:
            form["scope"] = scope
        data = await self._form_request("/v1/oauth/token", data=form)
        return OAuthTokenResponse.from_dict(data)

    def oauth_build_authorize_url(
        self,
        client_id: str,
        redirect_uri: str,
        scope: str = "",
        state: str = "",
    ) -> OAuthAuthorizeResult:
        """Build an authorization URL with PKCE.

        This method is synchronous (not a coroutine) because it performs no I/O.
        The state parameter is required by the Wordmade ID server for CSRF
        protection. Generate a unique, unpredictable value and verify it
        when handling the callback.
        """
        if not state:
            raise ValueError("state parameter is required")
        verifier, challenge = _generate_pkce()
        params: dict[str, str] = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
        if scope:
            params["scope"] = scope
        url = f"{self._base_url}/v1/oauth/authorize?{urlencode(params)}"
        return OAuthAuthorizeResult(url=url, code_verifier=verifier)

    async def oauth_exchange_code(
        self,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> OAuthTokenResponse:
        """Exchange an authorization code for tokens (RFC 6749 §4.1.3)."""
        form = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }
        data = await self._form_request("/v1/oauth/token", data=form)
        return OAuthTokenResponse.from_dict(data)

    async def oauth_refresh_token(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        scope: str = "",
    ) -> OAuthTokenResponse:
        """Exchange a refresh token for new tokens (RFC 6749 §6)."""
        form: dict[str, str] = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }
        if scope:
            form["scope"] = scope
        data = await self._form_request("/v1/oauth/token", data=form)
        return OAuthTokenResponse.from_dict(data)

    async def oauth_userinfo(self, access_token: str) -> OAuthUserInfoResponse:
        """Fetch agent claims from the userinfo endpoint."""
        if not access_token:
            raise ValueError("access_token is required")
        data = await self._request("GET", "/v1/oauth/userinfo", auth_key=access_token)
        return OAuthUserInfoResponse.from_dict(data)

    async def oauth_revoke(
        self,
        client_id: str,
        client_secret: str,
        token: str,
        token_type_hint: str = "",
    ) -> None:
        """Revoke an OAuth token (RFC 7009).

        Use this to revoke refresh tokens. Access tokens are stateless JWTs
        and cannot be revoked.
        """
        form: dict[str, str] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "token": token,
        }
        if token_type_hint:
            form["token_type_hint"] = token_type_hint
        await self._form_request("/v1/oauth/revoke", data=form)

    async def oauth_discovery(self) -> OAuthDiscoveryResponse:
        """Fetch the OpenID Connect discovery document. No auth required."""
        data = await self._request("GET", "/.well-known/openid-configuration")
        return OAuthDiscoveryResponse.from_dict(data)
