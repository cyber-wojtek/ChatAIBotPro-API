"""
ChatAIBotProClient — async client for chataibot.pro
"""
from __future__ import annotations

import json
import logging
import mimetypes
import uuid as _uuid
from collections.abc import AsyncIterator
from pathlib import Path

import aiohttp

from .constants import (
    BASE_URL,
    DEFAULT_CHAT_MODEL,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_VIDEO_MODEL,
    ChatModel,
    ImageModel,
    VideoGenerationType,
    VideoModel,
)
from .exceptions import (
    APIError,
    AuthenticationError,
    FileUploadError,
    RateLimitError,
    ValidationError,
)
from .session import ChatSession
from .types import (
    ContextInfo,
    ChatOutput,
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

logger = logging.getLogger("chataibotpro")

# ── URL constants ─────────────────────────────────────────────────────────────
_USER_URL               = f"{BASE_URL}/api/user"
_USER_ANSWERS_URL       = f"{BASE_URL}/api/user/answers-count/v2"
_CTX_URL                = f"{BASE_URL}/api/message/context"
_CTX_ID_URL             = f"{BASE_URL}/api/message/context/{{chat_id}}"
_CTX_CALC_URL           = f"{BASE_URL}/api/message/context/calculate"
_CTX_MODEL_URL          = f"{BASE_URL}/api/message/change-context-model"
_STREAM_URL             = f"{BASE_URL}/api/message/streaming"
_CHAT_MSG_URL           = f"{BASE_URL}/api/message/chat/{{chat_id}}"
_IMAGE_URL              = f"{BASE_URL}/api/image/generate"
_VIDEO_URL              = f"{BASE_URL}/api/video"
_GALLERY_URL            = f"{BASE_URL}/api/gallery"
_FILE_URL               = f"{BASE_URL}/api/file/parse-file-formdata"
_SUB_PRICE_URL          = f"{BASE_URL}/api/payment/subscription/price"
_SUB_TARIFF_URL         = f"{BASE_URL}/api/payment/subscription/tariff"
_TG_LINK_URL            = f"{BASE_URL}/api/connect-telegram/link"
_LOGOUT_URL             = f"{BASE_URL}/api/logout"
_LANDING_HELLO_URL      = f"{BASE_URL}/api/landing/hello"


def _resolve_model(
    model: str | ChatModel | ImageModel | VideoModel | None,
    default: str,
) -> str:
    if model is None:
        return default
    if isinstance(model, (ChatModel, ImageModel, VideoModel)):
        return model.value
    return str(model)


class ChatAIBotProClient:
    """
    Async client for chataibot.pro.

    Parameters
    ----------
    token:
        JWT token from the ``token`` cookie.  Obtain it by logging in via
        the browser and copying the cookie value.  Required for all API calls.
    timeout:
        Default request timeout in seconds (default 60).
    proxy:
        Optional HTTP/S proxy URL.

    Example::

        async with ChatAIBotProClient("eyJhbGci...") as client:
            async for chunk in client.stream_message("Hello!"):
                print(chunk.delta, end="", flush=True)
    """

    def __init__(
        self,
        token: str = "",
        timeout: int = 60,
        proxy: str | None = None,
    ) -> None:
        self._token   = token
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._proxy   = proxy
        self._session: aiohttp.ClientSession | None = None

    # ── headers / session ─────────────────────────────────────────────────

    def _build_headers(self) -> dict[str, str]:
        return {
            "Content-Type":          "application/json",
            "Accept":                "*/*",
            "x-distribution-channel": "web",
            "Origin":                "https://chataibot.pro",
            "Referer":               "https://chataibot.pro/app/chat",
            "User-Agent":            (
                "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) "
                "Gecko/20100101 Firefox/150.0"
            ),
            "Cookie":                f"chakra-ui-color-mode=dark; token={self._token}",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            if not self._token:
                raise AuthenticationError(
                    "No token set.  Pass token= to ChatAIBotProClient()."
                )
            self._session = aiohttp.ClientSession(
                headers=self._build_headers(),
                connector=aiohttp.TCPConnector(ssl=True),
            )
        return self._session

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("ChatAIBotProClient session closed.")

    async def __aenter__(self) -> "ChatAIBotProClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    # ── error handling ────────────────────────────────────────────────────

    @staticmethod
    async def _raise_for_status(resp: aiohttp.ClientResponse) -> None:
        if resp.status == 401:
            raise AuthenticationError("Invalid or expired token.")
        if resp.status == 422:
            body = await resp.json(content_type=None)
            raise ValidationError(
                body.get("message", "Validation error"),
                details=body.get("details", []),
            )
        if resp.status == 429:
            ra = resp.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded.",
                retry_after_s=int(ra) if ra and ra.isdigit() else None,
            )
        if resp.status >= 400:
            body = await resp.text()
            raise APIError(f"HTTP {resp.status}: {body[:400]}", status_code=resp.status)

    # ── low-level helpers ─────────────────────────────────────────────────

    async def _post(self, url: str, payload: dict) -> dict:
        session = await self._get_session()
        async with session.post(
            url,
            data=json.dumps(payload).encode(),
            timeout=self._timeout,
            proxy=self._proxy,
        ) as resp:
            await self._raise_for_status(resp)
            return await resp.json(content_type=None)

    async def _get(self, url: str, params: dict | None = None) -> dict | list:
        session = await self._get_session()
        async with session.get(
            url,
            params=params,
            timeout=self._timeout,
            proxy=self._proxy,
        ) as resp:
            await self._raise_for_status(resp)
            return await resp.json(content_type=None)

    async def _post_logout(self, url: str) -> None:
        session = await self._get_session()
        async with session.post(
            url,
            timeout=self._timeout,
            proxy=self._proxy,
        ) as resp:
            await self._raise_for_status(resp)

    # ── SSE streaming ─────────────────────────────────────────────────────

    async def _stream_sse(self, url: str, payload: dict) -> AsyncIterator[dict]:
        """POST *payload* and yield parsed SSE event dicts."""
        session = await self._get_session()
        async with session.post(
            url,
            data=json.dumps(payload).encode(),
            headers={"Accept": "text/event-stream"},
            timeout=aiohttp.ClientTimeout(total=3600),
            proxy=self._proxy,
        ) as resp:
            if resp.status >= 400:
                await self._raise_for_status(resp)

            buf = ""
            async for raw in resp.content:
                buf += raw.decode("utf-8", errors="replace")
                while "\n\n" in buf:
                    block, buf = buf.split("\n\n", 1)
                    event_type: str | None = None
                    data_str:   str | None = None
                    for line in block.splitlines():
                        line = line.strip()
                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                    if data_str:
                        try:
                            parsed = json.loads(data_str)
                            yield {"event": event_type or "data", "data": parsed}
                        except json.JSONDecodeError:
                            # Plain text delta (some SSE streams send raw text)
                            yield {"event": event_type or "data", "data": {"text": data_str}}

    # ══════════════════════════════════════════════════════════════════════
    # AUTH
    # ══════════════════════════════════════════════════════════════════════

    async def logout(self) -> None:
        """POST /api/logout — invalidate the current session server-side."""
        await self._post_logout(_LOGOUT_URL)
        logger.info("Logged out.")

    # ══════════════════════════════════════════════════════════════════════
    # USER
    # ══════════════════════════════════════════════════════════════════════

    async def get_current_user(self) -> UserRecord:
        """
        Fetch the authenticated user profile (GET /api/user).

        Returns
        -------
        UserRecord
        """
        data = await self._get(_USER_URL)
        u    = data.get("user", data) if isinstance(data, dict) else {}
        return UserRecord(
            user_id    = u.get("id", 0),
            email      = u.get("email", ""),
            first_name = u.get("firstnameWeb", u.get("firstname", "")),
            last_name  = u.get("lastnameWeb",  u.get("lastname",  "")),
            plan       = (u.get("settings") or {}).get("plan", ""),
            token      = u.get("token", self._token),
            metadata   = u,
        )

    async def get_answers_count(self) -> dict:
        """
        Return usage stats from GET /api/user/answers-count/v2.

        Returns
        -------
        dict
            Raw response (request counts, limits, etc.).
        """
        return await self._get(_USER_ANSWERS_URL)  # type: ignore[return-value]

    # ══════════════════════════════════════════════════════════════════════
    # CONTEXT / CHAT CREATION
    # ══════════════════════════════════════════════════════════════════════

    async def create_context(
        self,
        title: str,
        model: str | ChatModel | None = None,
        from_: int = 1,
    ) -> ContextInfo:
        """
        Create a new server-side chat thread (POST /api/message/context).

        Parameters
        ----------
        title:
            Disfplay name / first message text.
        model:
            Chat model to use.
        from_:
            Source flag (1 = web).

        Returns
        -------
        ContextInfo
        """
        resolved = _resolve_model(model, DEFAULT_CHAT_MODEL)
        data = await self._post(_CTX_URL, {
            "title":     title,
            "chatModel": resolved,
            "from":      from_,
        })
        c = data.get("chat", data)
        return ContextInfo(
            chat_id  = c.get("id", 0),
            title    = c.get("title", title),
            model    = c.get("model", resolved),
            metadata = c,
        )

    async def get_context(self, chat_id: int) -> dict:
        """
        GET /api/message/context/{chat_id} — fetch context metadata.
        """
        return await self._get(_CTX_ID_URL.format(chat_id=chat_id))  # type: ignore[return-value]

    async def calculate_tokens(
        self,
        text: str,
        chat_id: int = 0,
        model: str | ChatModel | None = None,
        promt_id: int | None = None,
    ) -> TokenUsage:
        """
        Estimate token/credit cost before sending (POST /api/message/context/calculate).

        Parameters
        ----------
        text:
            The message text to estimate.
        chat_id:
            Existing chat ID (0 for a new chat).
        model:
            Model to estimate for.

        Returns
        -------
        TokenUsage
        """
        resolved = _resolve_model(model, DEFAULT_CHAT_MODEL)
        data = await self._post(_CTX_CALC_URL, {
            "text":    text,
            "chatId":  chat_id,
            "promtId": promt_id,
            "model":   resolved,
        })
        return TokenUsage(
            token_count = data.get("tokenCount", data.get("tokens", 0)),
            credit_cost = data.get("creditCost", data.get("cost",   0.0)),
            metadata    = data,
        )

    async def change_context_model(
        self,
        chat_id: int,
        model: str | ChatModel | None = None,
        title: str | None = None,
        is_international: bool = True,
    ) -> dict:
        """
        Change the model of an existing chat (POST /api/message/change-context-model).
        """
        payload: dict = {
            "chatId":          chat_id,
            "isInternational": is_international,
        }
        if model is not None:
            payload["chatModel"] = _resolve_model(model, DEFAULT_CHAT_MODEL)
        if title is not None:
            payload["title"] = title
        return await self._post(_CTX_MODEL_URL, payload)

    # ══════════════════════════════════════════════════════════════════════
    # CHAT — STREAMING
    # ══════════════════════════════════════════════════════════════════════

    async def stream_message(
        self,
        text: str,
        *,
        chat_id: int = 0,
        model: str | ChatModel | None = None,
        with_potential_questions: bool = True,
        links: list[str] | None = None,
        skip_cloud_write: bool = False,
        from_: int = 1,
    ) -> AsyncIterator[ChatOutput]:
        """
        Stream a chat response via SSE (POST /api/message/streaming).

        If *chat_id* is 0 a new context is created automatically using
        *text* as the title.

        Parameters
        ----------
        text:
            User message.
        chat_id:
            Existing chat ID.  0 creates a new one.
        model:
            Model override.
        with_potential_questions:
            Request follow-up question suggestions.
        links:
            URLs to include in the context.

        Yields
        ------
        ChatOutput
            Incremental chunks.  ``chunk.delta`` is the new text;
            ``chunk.text`` is the full accumulated text.

        Example::

            async for chunk in client.stream_message("Hello!"):
                print(chunk.delta, end="", flush=True)
        """
        if chat_id == 0:
            ctx     = await self.create_context(text, model=model)
            chat_id = ctx.chat_id

        payload = {
            "text":                   text,
            "chatId":                 chat_id,
            "withPotentialQuestions": with_potential_questions,
            "linksToParse":           links or [],
            "skipCloudWrite":         skip_cloud_write,
            "from":                   from_,
        }

        accumulated = ""
        async for evt in self._stream_sse(_STREAM_URL, payload):
            data  = evt["data"]
            event = evt["event"]

            # Plain text delta
            if isinstance(data, dict) and "text" in data and event not in ("done", "error"):
                delta        = data["text"]
                accumulated += delta
                yield ChatOutput(
                    text    = accumulated,
                    delta   = delta,
                    chat_id = chat_id,
                    metadata = data,
                )

            # Structured delta (some versions)
            elif isinstance(data, dict) and "delta" in data:
                delta        = data["delta"]
                accumulated += delta
                yield ChatOutput(
                    text     = accumulated,
                    delta    = delta,
                    chat_id  = chat_id,
                    metadata = data,
                )

            # Final done event
            elif event == "done" or (isinstance(data, dict) and data.get("done")):
                pqs = data.get("potentialQuestions", []) if isinstance(data, dict) else []
                mid = data.get("messageId", "")         if isinstance(data, dict) else ""
                mdl = data.get("model", "")              if isinstance(data, dict) else ""
                yield ChatOutput(
                    text                 = accumulated,
                    delta                = "",
                    chat_id              = chat_id,
                    message_id           = mid,
                    model                = mdl,
                    potential_questions  = pqs,
                    metadata             = data if isinstance(data, dict) else {},
                )
                return

    async def send_message(
        self,
        text: str,
        *,
        chat_id: int = 0,
        model: str | ChatModel | None = None,
        with_potential_questions: bool = True,
        links: list[str] | None = None,
        skip_cloud_write: bool = False,
        from_: int = 1,
    ) -> ChatOutput:
        """
        Send a message and collect the full response (non-streaming wrapper).

        Returns
        -------
        ChatOutput
            Complete response with accumulated text.
        """
        final: ChatOutput | None = None
        async for chunk in self.stream_message(
            text,
            chat_id=chat_id,
            model=model,
            with_potential_questions=with_potential_questions,
            links=links,
            skip_cloud_write=skip_cloud_write,
            from_=from_,
        ):
            final = chunk
        return final or ChatOutput(text="", chat_id=chat_id)

    # ══════════════════════════════════════════════════════════════════════
    # CHAT — SESSION
    # ══════════════════════════════════════════════════════════════════════

    def start_chat(
        self,
        model: str | ChatModel | None = None,
        *,
        chat_id: int = 0,
        with_potential_questions: bool = True,
    ) -> ChatSession:
        """
        Create a stateful multi-turn :class:`ChatSession`.

        Parameters
        ----------
        model:
            Default model for all turns.
        chat_id:
            Resume an existing thread by ID.  0 = new thread.

        Example::

            chat = client.start_chat()
            r1 = await chat.send("My name is Alice.")
            r2 = await chat.send("What's my name?")
            print(r2.text)
        """
        return ChatSession(
            client  = self,
            model   = _resolve_model(model, DEFAULT_CHAT_MODEL),
            chat_id = chat_id,
            with_potential_questions = with_potential_questions,
        )

    # ══════════════════════════════════════════════════════════════════════
    # CHAT HISTORY
    # ══════════════════════════════════════════════════════════════════════

    async def get_chat_messages(self, chat_id: int) -> list[MessageRecord]:
        """
        Fetch message history for a chat (GET /api/message/chat/{chatId}).

        Returns
        -------
        list[MessageRecord]
        """
        data  = await self._get(_CHAT_MSG_URL.format(chat_id=chat_id))
        items = data.get("messages", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []
        return [
            MessageRecord(
                message_id = m.get("id",        ""),
                role       = m.get("role",       ""),
                content    = m.get("content",    m.get("text", "")),
                model      = m.get("model",      ""),
                created_at = m.get("createdAt",  ""),
                metadata   = m,
            )
            for m in items
        ]

    # ══════════════════════════════════════════════════════════════════════
    # IMAGE GENERATION
    # ══════════════════════════════════════════════════════════════════════

    async def generate_image(
        self,
        prompt: str,
        model: str | ImageModel | None = None,
        *,
        from_: int = 1,
        is_international: bool = True,
        request_id: str | None = None,
    ) -> ImageOutput:
        """
        Generate an image from a text prompt (POST /api/image/generate).

        Parameters
        ----------
        prompt:
            Image description.
        model:
            Image model.  Defaults to ``GPT_IMAGE_2``.
        request_id:
            Idempotency UUID.  Auto-generated if omitted.

        Returns
        -------
        ImageOutput

        Example::

            img = await client.generate_image(
                "A golden sunset over Warsaw, oil painting",
                model=ImageModel.FLUX_PRO,
            )
            await img.save("./outputs")
        """
        resolved  = _resolve_model(model, DEFAULT_IMAGE_MODEL)
        rid       = request_id or str(_uuid.uuid4())
        data      = await self._post(_IMAGE_URL, {
            "text":             prompt,
            "from":             from_,
            "generationType":   resolved,
            "requestId":        rid,
            "isInternational":  is_international,
        })
        img  = data.get("image", data)
        url  = (
            img.get("url", "")
            or img.get("imageUrl", "")
            or img.get("resultUrl", "")
        )
        return ImageOutput(
            url        = url,
            model      = resolved,
            request_id = rid,
            metadata   = data,
        )

    # ══════════════════════════════════════════════════════════════════════
    # VIDEO GENERATION
    # ══════════════════════════════════════════════════════════════════════

    async def generate_video(
        self,
        prompt: str,
        model: str | VideoModel | None = None,
        *,
        generation_type: str | VideoGenerationType = VideoGenerationType.TEXT_TO_VIDEO,
        duration: str = "5",
        image_url: str | None = None,
        camera_fixed: bool = False,
        is_international: bool = True,
        from_: int = 1,
    ) -> VideoOutput:
        """
        Generate a video from text or image (POST /api/video).

        Parameters
        ----------
        prompt:
            Video description.
        model:
            Video model.  Defaults to ``seedance-v1/lite``.
        generation_type:
            ``text-to-video`` or ``image-to-video``.
        duration:
            ``"5"`` or ``"10"`` seconds.
        image_url:
            Source image URL for image-to-video.

        Returns
        -------
        VideoOutput

        Example::

            video = await client.generate_video(
                "A drone shot over Warsaw at sunset",
                model=VideoModel.KLING_2_6_PRO,
                duration="5",
            )
            await video.save("./outputs")
        """
        resolved = _resolve_model(model, DEFAULT_VIDEO_MODEL)
        gt       = (
            generation_type.value
            if isinstance(generation_type, VideoGenerationType)
            else str(generation_type)
        )
        payload: dict = {
            "promt":               prompt,
            "modelVersion":        resolved,
            "generationType":      gt,
            "from":                from_,
            "duration":            duration,
            "seedanceCameraFixed": camera_fixed,
            "isInternational":     is_international,
        }
        if image_url:
            payload["imageUrl"] = image_url

        data   = await self._post(_VIDEO_URL, payload)
        vid    = data.get("video", data)
        url    = vid.get("url", vid.get("videoUrl", vid.get("resultUrl", "")))
        status = vid.get("status", "")
        return VideoOutput(
            url      = url,
            model    = resolved,
            status   = status,
            metadata = data,
        )

    async def image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        model: str | VideoModel | None = None,
        *,
        duration: str = "5",
    ) -> VideoOutput:
        """
        Animate a still image into a video.

        Convenience wrapper around :meth:`generate_video` with
        ``generation_type=image-to-video``.
        """
        return await self.generate_video(
            prompt,
            model           = model,
            generation_type = VideoGenerationType.IMAGE_TO_VIDEO,
            duration        = duration,
            image_url       = image_url,
        )

    # ══════════════════════════════════════════════════════════════════════
    # GALLERY
    # ══════════════════════════════════════════════════════════════════════

    async def get_gallery(
        self,
        *,
        offset: int = 0,
        take_count: int = 25,
        is_image: bool = False,
        is_video: bool = False,
    ) -> list[GalleryRecord]:
        """
        Fetch generated media from the gallery (POST /api/gallery).

        Parameters
        ----------
        offset:
            Pagination offset.
        take_count:
            Items per page (max 25).
        is_image:
            Return images only.
        is_video:
            Return videos only.

        Returns
        -------
        list[GalleryRecord]
        """
        payload: dict = {"offset": offset, "takeCount": take_count}
        if is_image:
            payload["isImage"] = True
        if is_video:
            payload["isVideo"] = True

        data  = await self._post(_GALLERY_URL, payload)
        items = data.get("items", data.get("gallery", [])) if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []

        records: list[GalleryRecord] = []
        for item in items:
            url      = item.get("imageUrl", item.get("videoUrl", item.get("url", "")))
            thumb    = item.get("thumbUrl", item.get("thumbnailUrl", ""))
            is_vid   = bool(item.get("isVideo", False) or item.get("videoUrl"))
            records.append(GalleryRecord(
                record_id  = str(item.get("id", "")),
                url        = url,
                thumb_url  = thumb,
                prompt     = item.get("promt", item.get("prompt", "")),
                model      = item.get("model", item.get("generationType", "")),
                is_video   = is_vid,
                created_at = item.get("createdAt", ""),
                metadata   = item,
            ))
        return records

    async def get_image_gallery(
        self, offset: int = 0, take_count: int = 25
    ) -> list[GalleryRecord]:
        """Return image gallery items."""
        return await self.get_gallery(offset=offset, take_count=take_count, is_image=True)

    async def get_video_gallery(
        self, offset: int = 0, take_count: int = 25
    ) -> list[GalleryRecord]:
        """Return video gallery items."""
        return await self.get_gallery(offset=offset, take_count=take_count, is_video=True)

    # ══════════════════════════════════════════════════════════════════════
    # FILE UPLOAD
    # ══════════════════════════════════════════════════════════════════════

    async def upload_file(
        self,
        file_path: str | Path | None = None,
        *,
        data: bytes | None = None,
        filename: str = "file",
        mime_type: str | None = None,
    ) -> FileRecord:
        """
        Upload and parse a file (POST /api/file/parse-file-formdata).

        The server extracts the text content from the file so it can be
        included in chat context.

        Parameters
        ----------
        file_path:
            Local file path.
        data:
            Raw bytes (alternative to *file_path*).
        filename:
            File name to use when uploading raw bytes.
        mime_type:
            MIME type; auto-detected from *file_path* if omitted.

        Returns
        -------
        FileRecord

        Example::

            rec = await client.upload_file("report.pdf")
            r   = await client.send_message(
                "Summarise this document.",
                chat_id=chat.chat_id,
            )
        """
        if data is None:
            path      = Path(file_path)  # type: ignore[arg-type]
            mime_type = mime_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            data      = path.read_bytes()
            filename  = path.name
        mime_type = mime_type or "application/octet-stream"

        session = await self._get_session()

        # Remove Content-Type so aiohttp sets multipart boundary
        old_ct = session._default_headers.pop("Content-Type", None)
        try:
            form = aiohttp.FormData()
            form.add_field("file", data, filename=filename, content_type=mime_type)

            async with session.post(
                _FILE_URL,
                data     = form,
                timeout  = aiohttp.ClientTimeout(total=120),
                proxy    = self._proxy,
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise FileUploadError(f"Upload failed ({resp.status}): {body[:300]}")
                result = await resp.json(content_type=None)
        finally:
            if old_ct is not None:
                session._default_headers["Content-Type"] = old_ct

        return FileRecord(
            file_id  = str(result.get("id", result.get("fileId", ""))),
            filename = result.get("filename", filename),
            content  = result.get("content", result.get("text", "")),
            metadata = result,
        )

    # ══════════════════════════════════════════════════════════════════════
    # SUBSCRIPTION & PRICING
    # ══════════════════════════════════════════════════════════════════════

    async def get_subscription_prices(
        self,
        payment_type: str = "STRIPE_BANK_CARD",
    ) -> SubscriptionPrice:
        """
        Fetch subscription pricing (POST /api/payment/subscription/price).

        Parameters
        ----------
        payment_type:
            ``"STRIPE_BANK_CARD"`` (default) or other supported types.

        Returns
        -------
        SubscriptionPrice
        """
        data = await self._post(_SUB_PRICE_URL, {"paymentType": payment_type})
        prices = data.get("prices", data.get("plans", [data] if isinstance(data, dict) else data))
        return SubscriptionPrice(
            prices   = prices if isinstance(prices, list) else [prices],
            metadata = data if isinstance(data, dict) else {},
        )

    async def get_subscription_tariff(
        self,
        origin: int = 1,
    ) -> TariffInfo:
        """
        Fetch tariff / plan details (GET /api/payment/subscription/tariff).

        Returns
        -------
        TariffInfo
        """
        data    = await self._get(_SUB_TARIFF_URL, params={"origin": str(origin)})
        tariffs = data.get("tariffs", data.get("plans", [])) if isinstance(data, dict) else data
        return TariffInfo(
            tariffs  = tariffs if isinstance(tariffs, list) else [tariffs],
            metadata = data if isinstance(data, dict) else {},
        )

    # ══════════════════════════════════════════════════════════════════════
    # TELEGRAM
    # ══════════════════════════════════════════════════════════════════════

    async def get_telegram_link(
        self,
        is_international: bool = True,
    ) -> str:
        """
        Get the Telegram connection link (GET /api/connect-telegram/link).

        Returns
        -------
        str
            Deep-link URL for connecting Telegram.
        """
        data = await self._get(
            _TG_LINK_URL,
            params={"isInternational": "true" if is_international else "false"},
        )
        if isinstance(data, dict):
            return data.get("link", data.get("url", str(data)))
        return str(data)

    # ══════════════════════════════════════════════════════════════════════
    # LANDING
    # ══════════════════════════════════════════════════════════════════════

    async def landing_hello(self) -> dict:
        """
        GET /api/landing/hello — lightweight ping / landing data.

        Returns
        -------
        dict
        """
        return await self._get(_LANDING_HELLO_URL)  # type: ignore[return-value]
