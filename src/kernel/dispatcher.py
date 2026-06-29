from __future__ import annotations

from typing import Any, Protocol

from contracts.event import Event, EventType

from .event_bus import EventBus


class Handler(Protocol):
    """Contrat minimal d'un handler d'événement."""

    async def handle(self, event: Event) -> Any:
        """Traite un événement et retourne une réponse coopérative."""

        ...


class Dispatcher:
    """Route un Event vers son handler et publie une copie observable.

    Le Dispatcher résout toujours les Request. Un événement sans handler ne
    bloque donc jamais un composant : il reçoit une réponse explicite
    ``handled=False``.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.handlers: dict[EventType, Handler] = {}
        self.event_bus = event_bus

    def register(self, event_type: EventType, handler: Handler) -> None:
        """Associe un type d'événement à un handler."""

        self.handlers[event_type] = handler

    async def dispatch(self, event: Event) -> Any:
        """Publie puis route un événement."""

        await self.event_bus.publish(event)
        handler = self.handlers.get(event.type)

        try:
            if handler is None:
                result: Any = {
                    "ok": True,
                    "handled": False,
                    "event": event.type.name,
                    "source": event.source,
                }
            else:
                result = await handler.handle(event)

            self._resolve_request(event, result)
            return result
        except BaseException as exc:
            self._reject_request(event, exc)
            raise

    @staticmethod
    def _resolve_request(event: Event, result: Any) -> None:
        if event.request and event.request.reply and not event.request.reply.done():
            event.request.reply.set_result(result)

    @staticmethod
    def _reject_request(event: Event, exc: BaseException) -> None:
        if event.request and event.request.reply and not event.request.reply.done():
            event.request.reply.set_exception(exc)
