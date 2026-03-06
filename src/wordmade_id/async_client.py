"""Asynchronous client for the Wordmade ID API."""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

import httpx

from .constants import DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from .errors import classify_error
from .types import (
    Agent,
    AvatarResponse,
    CustomFieldsResponse,
    DirectoryPage,
    DirectoryStats,
    MetadataEntry,
    MetadataListResponse,
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
        http_client: Optional[httpx.AsyncClient] = None,
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
        json_body: Optional[object] = None,
        params: Optional[dict[str, str]] = None,
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
                message = data.get("message", resp.text)
            except Exception:
                code = "unknown"
                message = resp.text
            raise classify_error(resp.status_code, code, message)

        return resp.json()  # type: ignore[no-any-return]

    # ------------------------------------------------------------------
    # Read-only (no auth required)
    # ------------------------------------------------------------------

    async def lookup(self, identifier: str) -> Agent:
        """Fetch a public agent profile by UUID or @@handle."""
        path = f"/v1/agents/{quote(identifier, safe='@')}"
        data = await self._request("GET", path)
        return Agent.from_dict(data)

    async def search(
        self, params: Optional[SearchParams] = None, **kwargs: object
    ) -> DirectoryPage:
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
        data = await self._request(
            "POST", "/v1/verify", json_body=body, auth_key=self._service_key
        )
        return VerifyResult.from_dict(data)

    # ------------------------------------------------------------------
    # Agent operations (key in body, not Bearer)
    # ------------------------------------------------------------------

    async def register(self, request: RegisterRequest) -> RegisterResponse:
        """Register a new agent identity."""
        data = await self._request(
            "POST", "/v1/agents/register", json_body=request.to_dict()
        )
        return RegisterResponse.from_dict(data)

    async def issue_token(self, request: TokenRequest) -> TokenResponse:
        """Request a JWT identity token for an agent."""
        data = await self._request(
            "POST", "/v1/agents/token", json_body=request.to_dict()
        )
        return TokenResponse.from_dict(data)

    # ------------------------------------------------------------------
    # Agent profile (Bearer iak_ or ias_ via agent_key)
    # ------------------------------------------------------------------

    async def update_profile(self, agent_uuid: str, fields: ProfileUpdate) -> Agent:
        """Update an agent's public profile fields."""
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

    async def replace_skills(
        self, agent_uuid: str, skills: list[Skill]
    ) -> SkillsResponse:
        """Replace all skills for the agent. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/skills"
        body = {"skills": [s.to_dict() for s in skills]}
        data = await self._request(
            "PUT", path, json_body=body, auth_key=self._agent_key
        )
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

    async def set_custom_field(
        self, agent_uuid: str, key: str, value: str
    ) -> None:
        """Set a custom field on the agent's public profile. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/custom/{quote(key, safe='')}"
        await self._request(
            "PUT", path, json_body={"value": value}, auth_key=self._agent_key
        )

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

    async def list_private_metadata(
        self, agent_uuid: str
    ) -> MetadataListResponse:
        """List all private metadata keys and values. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/private"
        data = await self._request("GET", path, auth_key=self._agent_key)
        return MetadataListResponse.from_dict(data)

    async def get_private_metadata(
        self, agent_uuid: str, key: str
    ) -> MetadataEntry:
        """Get a single private metadata value. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/private/{quote(key, safe='')}"
        data = await self._request("GET", path, auth_key=self._agent_key)
        return MetadataEntry.from_dict(data)

    async def set_private_metadata(
        self, agent_uuid: str, key: str, value: str
    ) -> None:
        """Set a private metadata value. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/private/{quote(key, safe='')}"
        await self._request(
            "PUT", path, json_body={"value": value}, auth_key=self._agent_key
        )

    async def delete_private_metadata(
        self, agent_uuid: str, key: str
    ) -> None:
        """Remove a private metadata key. Requires agent_key."""
        path = f"/v1/agents/{quote(agent_uuid, safe='')}/private/{quote(key, safe='')}"
        await self._request("DELETE", path, auth_key=self._agent_key)

    # ------------------------------------------------------------------
    # Sessions (iak_ only for create, iak_/ias_ for revoke)
    # ------------------------------------------------------------------

    async def create_session(self) -> SessionResponse:
        """Create a short-lived agent session token (ias_, 30 min TTL)."""
        data = await self._request(
            "POST", "/v1/agents/session", auth_key=self._agent_key
        )
        return SessionResponse.from_dict(data)

    async def revoke_session(self) -> None:
        """Revoke the current session (logout). Requires agent_key."""
        await self._request(
            "DELETE", "/v1/agents/session", auth_key=self._agent_key
        )

    # ------------------------------------------------------------------
    # Key Rotation (iak_ only)
    # ------------------------------------------------------------------

    async def rotate_key(self, agent_uuid: str) -> RotateKeyResponse:
        """Rotate the agent's API key. Requires agent_key set with iak_."""
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
                message = data.get("message", resp.text)
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
        """Initiate key recovery for an agent."""
        await self._request(
            "POST", "/v1/agents/recover", json_body=request.to_dict()
        )

    async def recover_confirm(
        self, request: RecoverConfirmRequest
    ) -> RecoverConfirmResponse:
        """Complete key recovery with the recovery token from email."""
        data = await self._request(
            "POST", "/v1/agents/recover/confirm", json_body=request.to_dict()
        )
        return RecoverConfirmResponse.from_dict(data)

    # ------------------------------------------------------------------
    # Registry (public, A2A agent card registry)
    # ------------------------------------------------------------------

    async def get_registry(
        self, params: Optional[RegistryParams] = None
    ) -> RegistryPage:
        """Query the A2A agent card registry with optional filters."""
        query = params.to_query() if params else {}
        data = await self._request("GET", "/v1/registry", params=query or None)
        return RegistryPage.from_dict(data)
