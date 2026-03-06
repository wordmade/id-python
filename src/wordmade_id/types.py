"""Response and request types for the Wordmade ID SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
    capabilities: List[str] = field(default_factory=list)
    verification: Dict[str, Any] = field(default_factory=dict)
    custom: Dict[str, str] = field(default_factory=dict)
    world_presences: List[WorldPresence] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Agent:
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

    agents: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    pages: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DirectoryPage:
        return cls(
            agents=data.get("agents", []),
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
    capabilities: Dict[str, int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DirectoryStats:
        return cls(
            total_agents=data.get("total_agents", 0),
            certified_today=data.get("certified_today", 0),
            capabilities=data.get("capabilities", {}),
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
    capabilities: List[str] = field(default_factory=list)
    cert_score: float = 0.0
    cert_level: int = 0
    certified_at: str = ""
    audience: str = ""
    issued_at: str = ""
    expires_at: str = ""
    error: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VerifyResult:
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
            certified_at=data.get("certified_at", ""),
            audience=data.get("audience", ""),
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
    capabilities: List[str] = field(default_factory=list)
    recovery_email: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
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
    def from_dict(cls, data: Dict[str, Any]) -> RegisterResponse:
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
    scope: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenResponse:
        return cls(
            token=data.get("token", ""),
            expires_at=data.get("expires_at", ""),
        )


@dataclass
class ProfileUpdate:
    """Mutable fields for updating an agent profile. Only set fields are sent."""

    name: Optional[str] = None
    bio_oneliner: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    business: Optional[str] = None
    capabilities: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
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

    def to_query(self) -> Dict[str, str]:
        params: Dict[str, str] = {}
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
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"id": self.id, "name": self.name}
        if self.description:
            d["description"] = self.description
        if self.tags:
            d["tags"] = self.tags
        if self.examples:
            d["examples"] = self.examples
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Skill:
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

    skills: List[Skill]
    count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SkillsResponse:
        return cls(
            skills=[Skill.from_dict(s) for s in data.get("skills", [])],
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
    def from_dict(cls, data: Dict[str, Any]) -> CustomField:
        return cls(
            key=data.get("key", ""),
            value=data.get("value", ""),
            updated_at=data.get("updated_at", ""),
            well_known=data.get("well_known", False),
        )


@dataclass
class CustomFieldsResponse:
    """Response from listing custom fields."""

    fields: List[CustomField]
    count: int
    quota: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CustomFieldsResponse:
        return cls(
            fields=[CustomField.from_dict(f) for f in data.get("fields", [])],
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
    def from_dict(cls, data: Dict[str, Any]) -> WellKnownField:
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

    fields: List[WellKnownField]
    count: int
    note: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WellKnownFieldsResponse:
        return cls(
            fields=[WellKnownField.from_dict(f) for f in data.get("fields", [])],
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
    def from_dict(cls, data: Dict[str, Any]) -> MetadataEntry:
        return cls(
            key=data.get("key", ""),
            value=data.get("value", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class MetadataListResponse:
    """Response from listing private metadata."""

    keys: List[MetadataEntry]
    count: int
    quota: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MetadataListResponse:
        return cls(
            keys=[MetadataEntry.from_dict(k) for k in data.get("keys", [])],
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
    def from_dict(cls, data: Dict[str, Any]) -> SessionResponse:
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
    def from_dict(cls, data: Dict[str, Any]) -> RotateKeyResponse:
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
    def from_dict(cls, data: Dict[str, Any]) -> AvatarResponse:
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

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"cert_token": self.cert_token}
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

    def to_dict(self) -> Dict[str, Any]:
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
    def from_dict(cls, data: Dict[str, Any]) -> RecoverConfirmResponse:
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

    def to_query(self) -> Dict[str, str]:
        params: Dict[str, str] = {}
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

    cards: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    pages: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RegistryPage:
        return cls(
            cards=data.get("cards", []),
            total=data.get("total", 0),
            page=data.get("page", 0),
            per_page=data.get("per_page", 0),
            pages=data.get("pages", 0),
        )
