"""Error types for the Wordmade ID SDK."""

from __future__ import annotations


class WordmadeIDError(Exception):
    """Base exception for all Wordmade ID SDK errors."""


class APIError(WordmadeIDError):
    """Non-2xx response from the Wordmade ID API."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"id-api {status_code}: {code} — {message}")


class NotFoundError(APIError):
    """Agent not found (404)."""

    def __init__(self, code: str = "agent_not_found", message: str = "Not found") -> None:
        super().__init__(404, code, message)


class UnauthorizedError(APIError):
    """Authentication failed (401)."""

    def __init__(self, code: str = "unauthorized", message: str = "Unauthorized") -> None:
        super().__init__(401, code, message)


class ForbiddenError(APIError):
    """Access denied (403)."""

    def __init__(self, code: str = "forbidden", message: str = "Forbidden") -> None:
        super().__init__(403, code, message)


class RateLimitedError(APIError):
    """Rate limit exceeded (429)."""

    def __init__(self, code: str = "rate_limited", message: str = "Rate limited") -> None:
        super().__init__(429, code, message)


def classify_error(status_code: int, code: str, message: str) -> APIError:
    """Create the appropriate error subclass based on HTTP status code."""
    if status_code == 404:
        return NotFoundError(code, message)
    if status_code == 401:
        return UnauthorizedError(code, message)
    if status_code == 403:
        return ForbiddenError(code, message)
    if status_code == 429:
        return RateLimitedError(code, message)
    return APIError(status_code, code, message)
