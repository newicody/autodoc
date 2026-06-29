from __future__ import annotations

from typing import Any

from contracts.event import Event, EventType
from .dispatcher import Dispatcher


class LifecycleManager:
    @staticmethod
    def register_handlers(dispatcher: Dispatcher) -> None:
        dispatcher.register(EventType.LOAD, PrintHandler("LOAD"))
        dispatcher.register(EventType.START, PrintHandler("START"))
        dispatcher.register(EventType.STOP, PrintHandler("STOP"))
        dispatcher.register(EventType.ERROR, PrintHandler("ERROR"))
        dispatcher.register(EventType.TICK, TickHandler())
        dispatcher.register(EventType.CONTEXT_REQUEST, PrintHandler("CONTEXT_REQUEST"))
        dispatcher.register(EventType.CONTEXT_REPLY, PrintHandler("CONTEXT_REPLY"))


class PrintHandler:
    def __init__(self, label: str) -> None:
        self.label = label

    async def handle(self, event: Event) -> Any:
        print(f"[Lifecycle] {self.label}: {event.source} -> {event.dest} payload={event.payload!r}")
        return {"ok": True, "event": self.label}


class TickHandler:
    async def handle(self, event: Event) -> Any:
        print(f"[Tick] {event.source}: {event.payload!r}")
        return {"ok": True, "handled": "TICK", "payload": event.payload}
