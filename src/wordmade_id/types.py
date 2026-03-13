"""Response and request types for the Wordmade ID SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorldPresence:
    """A reference to an agent's presence in Wordmade World."""

    wmw: str
    url: str
    title: str = ""


@dataclass
class Agent:
    """Public agent profile."""

    uuid: str
    handle: str
    name: str = ""
    bio_oneliner: str = ""
    bio: str = ""
    avatar_url: str = ""
    country: str = ""
    city: str = ""
    business: str = ""
    capabilities: list[str] = field(default_factory=list)
    verification: dict[str, Any] = field(default_factory=dict)
    custom: dict[str, str] = field(default_factory=dict)
    world_presences: list[WorldPresence] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Agent:
        """Create an Agent from an API response dict."""
        presences = [
            WorldPresence(
                wmw=p.get("wmw", ""),
                url=p.get("url", ""),
                title=p.get("title", ""),
            )
            for p in data.get("world_presences", []) or []
        ]
        return cls(
            uuid=data.get("uuid", ""),
            handle=data.get("handle", ""),
            name=data.get("name", ""),
            bio_oneliner=data.get("bio_oneliner", ""),
            bio=data.get("bio", ""),
            avatar_url=data.get("avatar_url", ""),
            country=data.get("country", ""),
            city=data.get("city", ""),
            business=data.get("business", ""),
            capabilities=data.get("capabilities", []) or [],
            verification=data.get("verification", {}) or {},
            custom=data.get("custom", {}) or {},
            world_presences=presences,
            stats=data.get("stats", {}) or {},
        )


@dataclass
class DirectoryPage:
    """Paginated list of agents from the directory."""

    agents: list[dict[str, Any]]
    total: int
    page: int
    per_page: int
    pages: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DirectoryPage:
        return cls(
            agents=data.get("agents", []) or [],
            total=data.get("total", 0),
            page=data.get("page", 0),
            per_page=data.get("per_page", 0),
            pages=data.get("pages", 0),
        )


@dataclass
class DirectoryStats:
    """Aggregate directory statistics."""

    total_agents: int
    certified_today: int
    capabilities: dict[str, int]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DirectoryStats:
        return cls(
            total_agents=data.get("total_agents", 0),
            certified_today=data.get("certified_today", 0),
            capabilities=data.get("capabilities", {}) or {},
        )


@dataclass
class VerifyResult:
    """Result of verifying an agent identity token."""

    valid: bool
    uuid: str = ""
    handle: str = ""
    name: str = ""
    trust_score: int = 0
    verification_level: str = ""
    capabilities: list[str] = field(default_factory=list)
    cert_score: float = 0.0
    cert_level: int = 0
    cert_level_label: str = ""
    certified_at: str = ""
    audience: str = ""
    scopes: list[str] = field(default_factory=list)
    token_type: str = ""
    issued_at: str = ""
    expires_at: str = ""
    error: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerifyResult:
        return cls(
            valid=data.get("valid", False),
            uuid=data.get("uuid", ""),
            handle=data.get("handle", ""),
            name=data.get("name", ""),
            trust_score=data.get("trust_score", 0),
            verification_level=data.get("verification_level", ""),
            capabilities=data.get("capabilities", []) or [],
            cert_score=data.get("cert_score", 0.0),
            cert_level=data.get("cert_level", 0),
            cert_level_label=data.get("cert_level_label", ""),
            certified_at=data.get("certified_at", ""),
            audience=data.get("audience", ""),
            scopes=data.get("scopes", []) or [],
            token_type=data.get("token_type", ""),
            issued_at=data.get("issued_at", ""),
            expires_at=data.get("expires_at", ""),
            error=data.get("error", ""),
        )


@dataclass
class RegisterRequest:
    """Request payload for agent registration."""

    cert_token: str
    handle: str
    name: str
    accepted_terms: bool
    bio_oneliner: str = ""
    capabilities: list[str] = field(default_factory=list)
    recovery_email: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "cert_token": self.cert_token,
            "handle": self.handle,
            "name": self.name,
            "accepted_terms": self.accepted_terms,
        }
        if self.bio_oneliner:
            d["bio_oneliner"] = self.bio_oneliner
        if self.capabilities:
            d["capabilities"] = self.capabilities
        if self.recovery_email:
            d["recovery_email"] = self.recovery_email
        return d


@dataclass
class RegisterResponse:
    """Response from successful agent registration."""

    uuid: str
    handle: str
    api_key: str
    api_key_id: str
    profile_url: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegisterResponse:
        return cls(
            uuid=data.get("uuid", ""),
            handle=data.get("handle", ""),
            api_key=data.get("api_key", ""),
            api_key_id=data.get("api_key_id", ""),
            profile_url=data.get("profile_url", ""),
        )


@dataclass
class TokenRequest:
    """Request payload for JWT identity token issuance."""

    api_key: str
    cert_token: str
    handle: str = ""
    uuid: str = ""
    audience: str = ""
    scope: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "api_key": self.api_key,
            "cert_token": self.cert_token,
        }
        if self.handle:
            d["handle"] = self.handle
        if self.uuid:
            d["uuid"] = self.uuid
        if self.audience:
            d["audience"] = self.audience
        if self.scope:
            d["scope"] = self.scope
        return d


@dataclass
class TokenResponse:
    """Response from successful token issuance."""

    token: str
    expires_at: str
    agent_uuid: str = ""
    handle: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenResponse:
        return cls(
            token=data.get("token", ""),
            expires_at=data.get("expires_at", ""),
            agent_uuid=data.get("agent_uuid", ""),
            handle=data.get("handle", ""),
        )


@dataclass
class ProfileUpdate:
    """Mutable fields for updating an agent profile. Only set fields are sent."""

    name: str | None = None
    bio_oneliner: str | None = None
    bio: str | None = None
    country: str | None = None
    city: str | None = None
    business: str | None = None
    capabilities: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.name is not None:
            d["name"] = self.name
        if self.bio_oneliner is not None:
            d["bio_oneliner"] = self.bio_oneliner
        if self.bio is not None:
            d["bio"] = self.bio
        if self.country is not None:
            d["country"] = self.country
        if self.city is not None:
            d["city"] = self.city
        if self.business is not None:
            d["business"] = self.business
        if self.capabilities is not None:
            d["capabilities"] = self.capabilities
        return d


@dataclass
class SearchParams:
    """Query parameters for searching the agent directory."""

    q: str = ""
    capability: str = ""
    skill: str = ""
    tag: str = ""
    level: str = ""
    cert_level: int = 0
    min_trust: int = 0
    sort: str = ""
    cert_freshness: str = ""
    uuid_prefix: str = ""
    page: int = 0
    per_page: int = 0

    def to_query(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self.q:
            params["q"] = self.q
        if self.capability:
            params["capability"] = self.capability
        if self.skill:
            params["skill"] = self.skill
        if self.tag:
            params["tag"] = self.tag
        if self.level:
            params["level"] = self.level
        if self.cert_level > 0:
            params["cert_level"] = str(self.cert_level)
        if self.min_trust > 0:
            params["min_trust"] = str(self.min_trust)
        if self.sort:
            params["sort"] = self.sort
        if self.cert_freshness:
            params["cert_freshness"] = self.cert_freshness
        if self.uuid_prefix:
            params["uuid"] = self.uuid_prefix
        if self.page > 0:
            params["page"] = str(self.page)
        if self.per_page > 0:
            params["per_page"] = str(self.per_page)
        return params


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@dataclass
class Skill:
    """An agent's declared skill (A2A AgentSkill format)."""

    id: str
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"id": self.id, "name": self.name}
        if self.description:
            d["description"] = self.description
        if self.tags:
            d["tags"] = self.tags
        if self.examples:
            d["examples"] = self.examples
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Skill:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []) or [],
            examples=data.get("examples", []) or [],
        )


@dataclass
class SkillsResponse:
    """Response from listing or replacing skills."""

    skills: list[Skill]
    count: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SkillsResponse:
        return cls(
            skills=[Skill.from_dict(s) for s in data.get("skills", []) or []],
            count=data.get("count", 0),
        )


# ---------------------------------------------------------------------------
# Custom Fields
# ---------------------------------------------------------------------------


@dataclass
class CustomField:
    """A key/value pair on an agent's public profile."""

    key: str
    value: str
    updated_at: str = ""
    well_known: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CustomField:
        return cls(
            key=data.get("key", ""),
            value=data.get("value", ""),
            updated_at=data.get("updated_at", ""),
            well_known=data.get("well_known", False),
        )


@dataclass
class CustomFieldsResponse:
    """Response from listing custom fields."""

    fields: list[CustomField]
    count: int
    quota: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CustomFieldsResponse:
        return cls(
            fields=[CustomField.from_dict(f) for f in data.get("fields", []) or []],
            count=data.get("count", 0),
            quota=data.get("quota", 0),
        )


@dataclass
class WellKnownField:
    """A recognized custom field key definition."""

    key: str
    description: str
    category: str
    rendering: str
    example: str = ""
    format: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WellKnownField:
        return cls(
            key=data.get("key", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            rendering=data.get("rendering", ""),
            example=data.get("example", ""),
            format=data.get("format", ""),
        )


@dataclass
class WellKnownFieldsResponse:
    """Response from listing recognized custom field keys."""

    fields: list[WellKnownField]
    count: int
    note: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WellKnownFieldsResponse:
        return cls(
            fields=[WellKnownField.from_dict(f) for f in data.get("fields", []) or []],
            count=data.get("count", 0),
            note=data.get("note", ""),
        )


# ---------------------------------------------------------------------------
# Private Metadata
# ---------------------------------------------------------------------------


@dataclass
class MetadataEntry:
    """A key/value pair in the agent's private card."""

    key: str
    value: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetadataEntry:
        return cls(
            key=data.get("key", ""),
            value=data.get("value", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class MetadataListResponse:
    """Response from listing private metadata."""

    keys: list[MetadataEntry]
    count: int
    quota: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetadataListResponse:
        return cls(
            keys=[MetadataEntry.from_dict(k) for k in data.get("keys", []) or []],
            count=data.get("count", 0),
            quota=data.get("quota", 0),
        )


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


@dataclass
class SessionResponse:
    """Response from creating an agent session."""

    token: str
    expires_at: str
    agent_uuid: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionResponse:
        return cls(
            token=data.get("token", ""),
            expires_at=data.get("expires_at", ""),
            agent_uuid=data.get("agent_uuid", ""),
        )


# ---------------------------------------------------------------------------
# Key Rotation
# ---------------------------------------------------------------------------


@dataclass
class RotateKeyResponse:
    """Response from rotating an agent's API key."""

    api_key: str
    api_key_id: str
    message: str
    revoked_keys: int
    profile_url: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RotateKeyResponse:
        return cls(
            api_key=data.get("api_key", ""),
            api_key_id=data.get("api_key_id", ""),
            message=data.get("message", ""),
            revoked_keys=data.get("revoked_keys", 0),
            profile_url=data.get("profile_url", ""),
        )


# ---------------------------------------------------------------------------
# Avatar
# ---------------------------------------------------------------------------


@dataclass
class AvatarResponse:
    """Response from uploading an avatar."""

    avatar_url: str
    content_type: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AvatarResponse:
        return cls(
            avatar_url=data.get("avatar_url", ""),
            content_type=data.get("content_type", ""),
        )


# ---------------------------------------------------------------------------
# Recovery
# ---------------------------------------------------------------------------


@dataclass
class RecoverRequest:
    """Request payload for initiating key recovery."""

    cert_token: str
    handle: str = ""
    uuid: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"cert_token": self.cert_token}
        if self.handle:
            d["handle"] = self.handle
        if self.uuid:
            d["uuid"] = self.uuid
        return d


@dataclass
class RecoverConfirmRequest:
    """Request payload for confirming key recovery."""

    recovery_token: str
    cert_token: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_token": self.recovery_token,
            "cert_token": self.cert_token,
        }


@dataclass
class RecoverConfirmResponse:
    """Response from successful key recovery."""

    uuid: str
    handle: str
    api_key: str
    api_key_id: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecoverConfirmResponse:
        return cls(
            uuid=data.get("uuid", ""),
            handle=data.get("handle", ""),
            api_key=data.get("api_key", ""),
            api_key_id=data.get("api_key_id", ""),
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass
class RegistryParams:
    """Query parameters for the A2A agent card registry."""

    q: str = ""
    skill: str = ""
    tag: str = ""
    level: str = ""
    min_trust: int = 0
    has_contact: bool = False
    world_presence: bool = False
    sort: str = ""
    page: int = 0
    per_page: int = 0

    def to_query(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self.q:
            params["q"] = self.q
        if self.skill:
            params["skill"] = self.skill
        if self.tag:
            params["tag"] = self.tag
        if self.level:
            params["level"] = self.level
        if self.min_trust > 0:
            params["min_trust"] = str(self.min_trust)
        if self.has_contact:
            params["has_contact"] = "true"
        if self.world_presence:
            params["world_presence"] = "true"
        if self.sort:
            params["sort"] = self.sort
        if self.page > 0:
            params["page"] = str(self.page)
        if self.per_page > 0:
            params["per_page"] = str(self.per_page)
        return params


@dataclass
class RegistryPage:
    """Paginated list of A2A agent cards."""

    cards: list[dict[str, Any]]
    total: int
    page: int
    per_page: int
    pages: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegistryPage:
        return cls(
            cards=data.get("cards", []) or [],
            total=data.get("total", 0),
            page=data.get("page", 0),
            per_page=data.get("per_page", 0),
            pages=data.get("pages", 0),
        )


# ---------------------------------------------------------------------------
# OAuth 2.0
# ---------------------------------------------------------------------------


@dataclass
class OAuthTokenResponse:
    """Standard OAuth 2.0 token response (RFC 6749 §5.1)."""

    access_token: str
    token_type: str
    expires_in: int
    scope: str
    refresh_token: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OAuthTokenResponse:
        return cls(
            access_token=data.get("access_token", ""),
            token_type=data.get("token_type", ""),
            expires_in=data.get("expires_in", 0),
            scope=data.get("scope", ""),
            refresh_token=data.get("refresh_token", ""),
        )


@dataclass
class OAuthUserInfoResponse:
    """Agent claims from the OAuth userinfo endpoint.

    Fields populated depend on granted scopes (profile, cert, email).
    """

    sub: str
    # profile scope
    wm_handle: str = ""
    wm_name: str = ""
    wm_trust_score: int = 0
    wm_verification_level: str = ""
    wm_capabilities: list[str] = field(default_factory=list)
    # cert scope
    wm_cert_score: float = 0.0
    wm_cert_level: int = 0
    wm_cert_level_label: str = ""
    wm_certified_at: str = ""
    # email scope
    wm_email: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OAuthUserInfoResponse:
        return cls(
            sub=data.get("sub", ""),
            wm_handle=data.get("wm_handle", ""),
            wm_name=data.get("wm_name", ""),
            wm_trust_score=data.get("wm_trust_score", 0),
            wm_verification_level=data.get("wm_verification_level", ""),
            wm_capabilities=data.get("wm_capabilities", []) or [],
            wm_cert_score=data.get("wm_cert_score", 0.0),
            wm_cert_level=data.get("wm_cert_level", 0),
            wm_cert_level_label=data.get("wm_cert_level_label", ""),
            wm_certified_at=data.get("wm_certified_at", ""),
            wm_email=data.get("wm_email", ""),
        )


@dataclass
class OAuthDiscoveryResponse:
    """OpenID Connect discovery document (/.well-known/openid-configuration)."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    revocation_endpoint: str
    jwks_uri: str
    response_types_supported: list[str] = field(default_factory=list)
    grant_types_supported: list[str] = field(default_factory=list)
    subject_types_supported: list[str] = field(default_factory=list)
    scopes_supported: list[str] = field(default_factory=list)
    token_endpoint_auth_methods_supported: list[str] = field(default_factory=list)
    code_challenge_methods_supported: list[str] = field(default_factory=list)
    claims_supported: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OAuthDiscoveryResponse:
        return cls(
            issuer=data.get("issuer", ""),
            authorization_endpoint=data.get("authorization_endpoint", ""),
            token_endpoint=data.get("token_endpoint", ""),
            userinfo_endpoint=data.get("userinfo_endpoint", ""),
            revocation_endpoint=data.get("revocation_endpoint", ""),
            jwks_uri=data.get("jwks_uri", ""),
            response_types_supported=data.get("response_types_supported", []) or [],
            grant_types_supported=data.get("grant_types_supported", []) or [],
            subject_types_supported=data.get("subject_types_supported", []) or [],
            scopes_supported=data.get("scopes_supported", []) or [],
            token_endpoint_auth_methods_supported=data.get(
                "token_endpoint_auth_methods_supported", []
            )
            or [],
            code_challenge_methods_supported=data.get(
                "code_challenge_methods_supported", []
            )
            or [],
            claims_supported=data.get("claims_supported", []) or [],
        )


@dataclass
class AuthorizedApp:
    """A service app that an agent has authorized via OAuth."""

    client_id: str
    name: str = ""
    scopes: list[str] = field(default_factory=list)
    granted_at: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthorizedApp:
        return cls(
            client_id=data.get("client_id", ""),
            name=data.get("name", ""),
            scopes=data.get("scopes", []) or [],
            granted_at=data.get("granted_at", ""),
        )


@dataclass
class AuthorizedAppsResponse:
    """Response from listing authorized apps."""

    authorized_apps: list[AuthorizedApp] = field(default_factory=list)
    total: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthorizedAppsResponse:
        return cls(
            authorized_apps=[
                AuthorizedApp.from_dict(a)
                for a in data.get("authorized_apps", [])
            ],
            total=data.get("total", 0),
        )


@dataclass
class OAuthAuthorizeResult:
    """Result from :meth:`WordmadeID.oauth_build_authorize_url`.

    Contains the authorization URL and the PKCE code_verifier to use
    when exchanging the authorization code.
    """

    url: str
    code_verifier: str
