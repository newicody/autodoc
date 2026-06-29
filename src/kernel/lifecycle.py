from __future__ import annotations

from typing import Any

from contracts.event import Event, EventType
from contracts.lifecycle import ComponentState

from .dispatcher import Dispatcher


class LifecycleManager:
    """Gestion minimale et observable du cycle de vie des composants."""

    def __init__(self) -> None:
        self.states: dict[str, ComponentState] = {}
        self.errors: dict[str, dict[str, Any]] = {}

    def register_handlers(self, dispatcher: Dispatcher) -> None:
        dispatcher.register(EventType.LOAD, LoadHandler(self))
        dispatcher.register(EventType.START, StartHandler(self))
        dispatcher.register(EventType.STOP, StopHandler(self))
        dispatcher.register(EventType.ERROR, ErrorHandler(self))
        dispatcher.register(EventType.TICK, TickHandler())

    def state_of(self, component_name: str) -> ComponentState | None:
        return self.states.get(component_name)


class LoadHandler:
    def __init__(self, lifecycle: LifecycleManager) -> None:
        self.lifecycle = lifecycle

    async def handle(self, event: Event) -> dict[str, Any]:
        self.lifecycle.states[event.source] = ComponentState.LOADED
        return {"ok": True, "handled": "LOAD", "source": event.source}


class StartHandler:
    def __init__(self, lifecycle: LifecycleManager) -> None:
        self.lifecycle = lifecycle

    async def handle(self, event: Event) -> dict[str, Any]:
        self.lifecycle.states[event.source] = ComponentState.STARTED
        return {"ok": True, "handled": "START", "source": event.source}


class StopHandler:
    def __init__(self, lifecycle: LifecycleManager) -> None:
        self.lifecycle = lifecycle

    async def handle(self, event: Event) -> dict[str, Any]:
        self.lifecycle.states[event.source] = ComponentState.STOPPED
        return {"ok": True, "handled": "STOP", "source": event.source}


class ErrorHandler:
    def __init__(self, lifecycle: LifecycleManager) -> None:
        self.lifecycle = lifecycle

    async def handle(self, event: Event) -> dict[str, Any]:
        error_payload = event.payload if isinstance(event.payload, dict) else {}
        self.lifecycle.states[event.source] = ComponentState.ERROR
        self.lifecycle.errors[event.source] = error_payload
        return {
            "ok": False,
            "handled": "ERROR",
            "source": event.source,
            "error": error_payload,
        }


class TickHandler:
    async def handle(self, event: Event) -> dict[str, Any]:
        return {
            "ok": True,
            "handled": "TICK",
            "source": event.source,
            "payload": event.payload,
        }
