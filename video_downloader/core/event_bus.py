"""Thread-safe event bus bridging worker threads to the asyncio UI loop.

Services call :meth:`EventBus.publish` from any thread. Events are marshalled
onto the asyncio loop with ``call_soon_threadsafe`` into an ``asyncio.Queue``;
a single consumer coroutine (:meth:`EventBus.pump`, started by the UI with
``page.run_task``) dispatches them to subscribed handlers. Handlers therefore
always run on the UI loop and may safely mutate Flet controls.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import TypeVar

from video_downloader.core.events import AppEvent

logger = logging.getLogger(__name__)

E = TypeVar("E", bound=AppEvent)


class EventBus:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[AppEvent] = asyncio.Queue()
        self._subscribers: dict[type[AppEvent], list[Callable[[AppEvent], None]]] = (
            defaultdict(list)
        )
        self._pending: list[AppEvent] = []  # published before the loop attached

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        for event in self._pending:
            self._queue.put_nowait(event)
        self._pending.clear()

    def publish(self, event: AppEvent) -> None:
        """Publish an event from any thread."""
        loop = self._loop
        if loop is None:
            self._pending.append(event)
            return
        loop.call_soon_threadsafe(self._queue.put_nowait, event)

    def subscribe(
        self, event_type: type[E], handler: Callable[[E], None]
    ) -> Callable[[], None]:
        """Register *handler* for events of *event_type* (and subclasses).

        Returns an unsubscribe callable.
        """
        handlers = self._subscribers[event_type]
        handlers.append(handler)  # type: ignore[arg-type]

        def unsubscribe() -> None:
            import contextlib

            with contextlib.suppress(ValueError):
                handlers.remove(handler)  # type: ignore[arg-type]

        return unsubscribe

    async def pump(self) -> None:
        """Consume events forever; run on the UI loop via ``page.run_task``."""
        while True:
            event = await self._queue.get()
            for event_type, handlers in list(self._subscribers.items()):
                if isinstance(event, event_type):
                    for handler in list(handlers):
                        try:
                            handler(event)
                        except Exception:
                            logger.exception("Event handler failed for %r", event)
