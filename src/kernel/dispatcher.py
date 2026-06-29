from __future__ import annotations

from typing import Any, Protocol

from contracts.event import Event, EventType
from .event_bus import EventBus


class Handler(Protocol):
    async def handle(self, event: Event) -> Any:
        ...


class Dispatcher:
    """Route un Event vers son handler et publie une copie observable."""

    def __init__(self, event_bus: EventBus) -> None:
        self.handlers: dict[EventType, Handler] = {}
        self.event_bus = event_bus

    def register(self, event_type: EventType, handler: Handler) -> None:
        self.handlers[event_type] = handler

    async def dispatch(self, event: Event) -> Any:
        await self.event_bus.publish(event)
        handler = self.handlers.get(event.type)
        result: Any = None

        try:
            if handler is not None:
                result = await handler.handle(event)

            if event.request and event.request.reply and not event.request.reply.done():
                event.request.reply.set_result(result)

            return result

        except BaseException as exc:
            if event.request and event.request.reply and not event.request.reply.done():
                event.request.reply.set_exception(exc)
            raise
