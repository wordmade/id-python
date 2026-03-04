"""Asynchronous client for the Wordmade ID API."""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

import httpx

from .constants import DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from .errors import classify_error
from .types import (
    Agent,
    DirectoryPage,
    DirectoryStats,
    ProfileUpdate,
    RegisterRequest,
    RegisterResponse,
    SearchParams,
    TokenRequest,
    TokenResponse,
    VerifyResult,
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
