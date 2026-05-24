"""Exceptions for chataibotpro_webapi."""
from __future__ import annotations


class ChatAIBotProError(Exception):
    """Base exception."""


class AuthenticationError(ChatAIBotProError):
    """Invalid or missing JWT token."""


class APIError(ChatAIBotProError):
    """Unexpected HTTP status from the API."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(ChatAIBotProError):
    """HTTP 429 — too many requests."""

    def __init__(self, message: str, retry_after_s: int | None = None) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s


class ValidationError(ChatAIBotProError):
    """HTTP 422 — request validation failed."""

    def __init__(self, message: str, details: list[dict] | None = None) -> None:
        super().__init__(message)
        self.details: list[dict] = details or []


class FileUploadError(ChatAIBotProError):
    """File upload / parse failed."""


class TimeoutError(ChatAIBotProError):
    """Request timed out."""
