"""
chataibotpro_webapi — Async Python client for chataibot.pro

Quick start::

    import asyncio
    from chataibotpro_webapi import ChatAIBotProClient

    async def main():
        async with ChatAIBotProClient("YOUR_JWT_TOKEN") as client:
            async for chunk in client.stream_message("Hello!"):
                print(chunk.delta, end="", flush=True)

    asyncio.run(main())
"""

from .client import ChatAIBotProClient
from .constants import ImageModel, VideoModel, VideoGenerationType
from .exceptions import (
    APIError,
    AuthenticationError,
    ChatAIBotProError,
    RateLimitError,
    ValidationError,
    FileUploadError,
    TimeoutError,
)
from .session import ChatSession
from .types import (
    ChatOutput,
    ContextInfo,
    FileRecord,
    GalleryRecord,
    ImageOutput,
    MessageRecord,
    SubscriptionPrice,
    TariffInfo,
    TokenUsage,
    UserRecord,
    VideoOutput,
)

import logging as _logging


def set_log_level(level: str) -> None:
    """Configure the ``chataibotpro`` logger."""
    log = _logging.getLogger("chataibotpro")
    log.handlers.clear()
    handler = _logging.StreamHandler()
    handler.setFormatter(
        _logging.Formatter("%(asctime)s  %(levelname)-5s  %(name)s  %(message)s")
    )
    log.addHandler(handler)
    log.setLevel(getattr(_logging, level.upper(), _logging.INFO))


__version__ = "1.0.1"

__all__ = [
    "ChatAIBotProClient",
    "ChatSession",
    # enums
    "ImageModel",
    "VideoModel",
    "VideoGenerationType",
    # types
    "ChatOutput",
    "ContextInfo",
    "FileRecord",
    "GalleryRecord",
    "ImageOutput",
    "MessageRecord",
    "SubscriptionPrice",
    "TariffInfo",
    "TokenUsage",
    "UserRecord",
    "VideoOutput",
    # exceptions
    "ChatAIBotProError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "FileUploadError",
    "TimeoutError",
    # logging
    "set_log_level",
]
