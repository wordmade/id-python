"""Synchronous client for the Wordmade ID API."""

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


class WordmadeID:
    """Synchronous client for the Wordmade ID agent identity API.

    Args:
        base_url: API base URL (default: https://api.id.wordmade.world).
        service_key: isk_ service key for verification calls.
        agent_key: iak_ or ias_ agent key for authenticated agent operations.
        timeout: HTTP request timeout in seconds.
        http_client: Custom httpx.Client instance.
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        service_key: str = "",
        agent_key: str = "",
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_key = service_key
        self._agent_key = agent_key
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        """Close the underlying HTTP client (only if we own it)."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> WordmadeID:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(
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

        resp = self._client.request(
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

    def lookup(self, identifier: str) -> Agent:
        """Fetch a public agent profile by UUID or @@handle."""
        path = f"/v1/agents/{quote(identifier, safe='@')}"
        data = self._request("GET", path)
        return Agent.from_dict(data)

    def search(self, params: Optional[SearchParams] = None, **kwargs: object) -> DirectoryPage:
        """Search the agent directory with optional filters."""
        if params is None:
            params = SearchParams(**kwargs)  # type: ignore[arg-type]
        data = self._request("GET", "/v1/directory", params=params.to_query())
        return DirectoryPage.from_dict(data)

    def get_stats(self) -> DirectoryStats:
        """Get aggregate directory statistics."""
        data = self._request("GET", "/v1/directory/stats")
        return DirectoryStats.from_dict(data)

    # ------------------------------------------------------------------
    # Verification (optional isk_ service key)
    # ------------------------------------------------------------------

    def verify(self, token: str, audience: str = "") -> VerifyResult:
        """Verify an agent's JWT identity token.

        Args:
            token: The JWT identity token to verify.
            audience: Optional audience claim to check.
        """
        body: dict[str, str] = {"token": token}
        if audience:
            body["audience"] = audience
        data = self._request("POST", "/v1/verify", json_body=body, auth_key=self._service_key)
        return VerifyResult.from_dict(data)

    # ------------------------------------------------------------------
    # Agent operations (key in body, not Bearer)
    # ------------------------------------------------------------------

    def register(self, request: RegisterRequest) -> RegisterResponse:
        """Register a new agent identity.

        The cert_token must contain a valid Wordmade Certification pass (wmn_ prefix).
        """
        data = self._request("POST", "/v1/agents/register", json_body=request.to_dict())
        return RegisterResponse.from_dict(data)

    def issue_token(self, request: TokenRequest) -> TokenResponse:
        """Request a JWT identity token for an agent.

        The API key is included in the request body (not as a Bearer header).
        """
        data = self._request("POST", "/v1/agents/token", json_body=request.to_dict())
        return TokenResponse.from_dict(data)

    # ------------------------------------------------------------------
    # Agent profile (Bearer iak_ or ias_ via agent_key)
    # ------------------------------------------------------------------

    def update_profile(self, agent_uuid: str, fields: ProfileUpdate) -> Agent:
        """Update an agent's public profile fields.

        Requires agent_key to be set (iak_ or ias_).
        """
        path = f"/v1/agents/{quote(agent_uuid, safe='')}"
        data = self._request(
            "PUT", path, json_body=fields.to_dict(), auth_key=self._agent_key
        )
        return Agent.from_dict(data)
