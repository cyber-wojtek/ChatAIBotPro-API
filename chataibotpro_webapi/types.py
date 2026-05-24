"""Return types for chataibotpro_webapi."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import aiohttp


async def _download(url: str, dest: Path) -> None:
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            r.raise_for_status()
            dest.write_bytes(await r.read())


# ── User ──────────────────────────────────────────────────────────────────────

@dataclass
class UserRecord:
    """Authenticated user profile from GET /api/user."""
    user_id:    int   = 0
    email:      str   = ""
    first_name: str   = ""
    last_name:  str   = ""
    plan:       str   = ""
    token:      str   = ""
    metadata:   dict  = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<UserRecord id={self.user_id} email={self.email!r} plan={self.plan!r}>"


@dataclass
class TokenUsage:
    """Response from POST /api/message/context/calculate."""
    token_count:    int   = 0
    credit_cost:    float = 0.0
    metadata:       dict  = field(default_factory=dict)


# ── Chat ──────────────────────────────────────────────────────────────────────

@dataclass
class ContextInfo:
    """Server-side chat context created by POST /api/message/context."""
    chat_id:   int  = 0
    title:     str  = ""
    model:     str  = ""
    metadata:  dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<ContextInfo chat_id={self.chat_id} model={self.model!r}>"


@dataclass
class ChatOutput:
    """
    A single streamed or complete chat response.

    Attributes
    ----------
    text:
        Full accumulated text so far.
    delta:
        New text in this chunk (streaming only).
    chat_id:
        Server chat ID.
    message_id:
        Server message UUID.
    model:
        Model that produced the response.
    potential_questions:
        Follow-up question suggestions (final chunk).
    metadata:
        Raw event data.
    """
    text:                str        = ""
    delta:               str        = ""
    chat_id:             int        = 0
    message_id:          str        = ""
    model:               str        = ""
    potential_questions: list[str]  = field(default_factory=list)
    metadata:            dict       = field(default_factory=dict)

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        preview = self.text[:100].replace("\n", " ")
        return f"<ChatOutput model={self.model!r} text={preview!r}>"


@dataclass
class MessageRecord:
    """A single message from GET /api/message/chat/{chatId}."""
    message_id: str  = ""
    role:       str  = ""
    content:    str  = ""
    model:      str  = ""
    created_at: str  = ""
    metadata:   dict = field(default_factory=dict)

    def __repr__(self) -> str:
        preview = self.content[:80].replace("\n", " ")
        return f"<MessageRecord role={self.role!r} content={preview!r}>"


# ── Images ────────────────────────────────────────────────────────────────────

@dataclass
class ImageOutput:
    """Result of POST /api/image/generate."""
    url:       str  = ""
    model:     str  = ""
    request_id: str = ""
    metadata:  dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<ImageOutput model={self.model!r} url={self.url!r}>"

    async def save(
        self,
        path: str | Path = ".",
        filename: str | None = None,
        verbose: bool = False,
    ) -> Path:
        dest_dir = Path(path)
        dest_dir.mkdir(parents=True, exist_ok=True)
        fname = filename or (self.url.split("/")[-1].split("?")[0] or "image.png")
        dest  = dest_dir / fname
        await _download(self.url, dest)
        if verbose:
            print(f"Saved: {dest.resolve()}")
        return dest.resolve()


# ── Video ─────────────────────────────────────────────────────────────────────

@dataclass
class VideoOutput:
    """Result of POST /api/video."""
    url:       str  = ""
    model:     str  = ""
    status:    str  = ""
    metadata:  dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<VideoOutput model={self.model!r} url={self.url!r}>"

    async def save(
        self,
        path: str | Path = ".",
        filename: str | None = None,
        verbose: bool = False,
    ) -> Path:
        dest_dir = Path(path)
        dest_dir.mkdir(parents=True, exist_ok=True)
        fname = filename or (self.url.split("/")[-1].split("?")[0] or "video.mp4")
        dest  = dest_dir / fname
        await _download(self.url, dest)
        if verbose:
            print(f"Saved: {dest.resolve()}")
        return dest.resolve()


# ── Gallery ───────────────────────────────────────────────────────────────────

@dataclass
class GalleryRecord:
    """A single item from POST /api/gallery."""
    record_id:   str  = ""
    url:         str  = ""
    thumb_url:   str  = ""
    prompt:      str  = ""
    model:       str  = ""
    is_video:    bool = False
    created_at:  str  = ""
    metadata:    dict = field(default_factory=dict)

    def __repr__(self) -> str:
        kind = "video" if self.is_video else "image"
        return f"<GalleryRecord {kind} model={self.model!r}>"

    async def save(
        self,
        path: str | Path = ".",
        filename: str | None = None,
        verbose: bool = False,
    ) -> Path:
        dest_dir = Path(path)
        dest_dir.mkdir(parents=True, exist_ok=True)
        src   = self.url
        ext   = "mp4" if self.is_video else "jpg"
        fname = filename or (src.split("/")[-1].split("?")[0] or f"media.{ext}")
        dest  = dest_dir / fname
        await _download(src, dest)
        if verbose:
            print(f"Saved: {dest.resolve()}")
        return dest.resolve()


# ── File ──────────────────────────────────────────────────────────────────────

@dataclass
class FileRecord:
    """Result of POST /api/file/parse-file-formdata."""
    file_id:   str  = ""
    filename:  str  = ""
    content:   str  = ""
    metadata:  dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<FileRecord filename={self.filename!r} id={self.file_id!r}>"


# ── Subscription ──────────────────────────────────────────────────────────────

@dataclass
class SubscriptionPrice:
    """Result of POST /api/payment/subscription/price."""
    prices:   list[dict] = field(default_factory=list)
    metadata: dict       = field(default_factory=dict)


@dataclass
class TariffInfo:
    """Result of GET /api/payment/subscription/tariff."""
    tariffs:  list[dict] = field(default_factory=list)
    metadata: dict       = field(default_factory=dict)
