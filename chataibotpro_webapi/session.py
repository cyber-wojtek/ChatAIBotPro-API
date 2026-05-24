"""Multi-turn ChatSession for chataibotpro_webapi."""
from __future__ import annotations
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from .types import ChatOutput

if TYPE_CHECKING:
    from .client import ChatAIBotProClient


class ChatSession:
    """
    Stateful multi-turn conversation.

    Do not instantiate directly — use :meth:`ChatAIBotProClient.start_chat`.

    Example::

        chat = client.start_chat()
        r1 = await chat.send("My name is Alice.")
        r2 = await chat.send("What is my name?")
        print(r2.text)
    """

    def __init__(
        self,
        client: "ChatAIBotProClient",
        model: str,
        chat_id: int = 0,
        with_potential_questions: bool = True,
    ) -> None:
        self._client  = client
        self._model   = model
        self._chat_id = chat_id
        self._wpq     = with_potential_questions
        self._turn    = 0
        self._last:   ChatOutput | None = None

    # ── properties ────────────────────────────────────────────────────────

    @property
    def chat_id(self) -> int:
        """Server-assigned chat ID (0 = not yet created)."""
        return self._chat_id

    @property
    def model(self) -> str:
        return self._model

    @property
    def turn_count(self) -> int:
        return self._turn

    @property
    def last_output(self) -> ChatOutput | None:
        return self._last

    # ── internal ──────────────────────────────────────────────────────────

    def _sync(self, output: ChatOutput) -> None:
        if output.chat_id and output.chat_id != self._chat_id:
            self._chat_id = output.chat_id
        self._last = output

    # ── public ────────────────────────────────────────────────────────────

    async def send(
        self,
        text: str,
        *,
        links: list[str] | None = None,
        model: str | None = None,
    ) -> ChatOutput:
        """Send *text* and await the complete response."""
        out = await self._client.send_message(
            text,
            chat_id=self._chat_id,
            model=model or self._model,
            with_potential_questions=self._wpq,
            links=links,
        )
        self._sync(out)
        self._turn += 1
        return out

    async def stream(
        self,
        text: str,
        *,
        links: list[str] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[ChatOutput]:
        """Stream the response to *text*."""
        async for chunk in self._client.stream_message(
            text,
            chat_id=self._chat_id,
            model=model or self._model,
            with_potential_questions=self._wpq,
            links=links,
        ):
            self._sync(chunk)
            yield chunk
        self._turn += 1

    async def get_history(self) -> list:
        """Fetch message history from the server."""
        if not self._chat_id:
            return []
        return await self._client.get_chat_messages(self._chat_id)

    def __repr__(self) -> str:
        return (
            f"ChatSession(model={self._model!r}, "
            f"chat_id={self._chat_id}, turns={self._turn})"
        )
