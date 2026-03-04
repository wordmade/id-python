"""Wordmade ID Python SDK — agent identity for AI agents."""

from ._version import __version__
from .async_client import AsyncWordmadeID
from .client import WordmadeID
from .errors import (
    APIError,
    ForbiddenError,
    NotFoundError,
    RateLimitedError,
    UnauthorizedError,
    WordmadeIDError,
)
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
    WorldPresence,
)

__all__ = [
    "__version__",
    "WordmadeID",
    "AsyncWordmadeID",
    "APIError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitedError",
    "UnauthorizedError",
    "WordmadeIDError",
    "Agent",
    "DirectoryPage",
    "DirectoryStats",
    "ProfileUpdate",
    "RegisterRequest",
    "RegisterResponse",
    "SearchParams",
    "TokenRequest",
    "TokenResponse",
    "VerifyResult",
    "WorldPresence",
]
