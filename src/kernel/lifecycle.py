from __future__ import annotations

from typing import Any

from contracts.event import Event, EventType
from contracts.lifecycle import ComponentState

from .dispatcher import Dispatcher


class LifecycleManager:
    """Gestionnaire minimal du cycle de vie Phase 1.

    Il reste un handler du kernel, pas une logique métier. Son rôle est de rendre
    les transitions observables et testables avant l'arrivée de services plus
    lourds comme OpenVINO, SQLite ou Qdrant.
    """

    def __init__(self) -> None:
        self.states: dict[str, ComponentState] = {}
        self.errors: dict[str, Any] = {}

    def register_handlers(self, dispatcher: Dispatcher) -> None:
        dispatcher.register(EventType.LOAD, _StateHandler(self, "LOAD", ComponentState.LOADED))
        dispatcher.register(EventType.START, _StateHandler(self, "START", ComponentState.STARTED))
        dispatcher.register(EventType.STOP, _StateHandler(self, "STOP", ComponentState.STOPPED))
        dispatcher.register(EventType.ERROR, _ErrorHandler(self))
        dispatcher.register(EventType.TICK, _TickHandler(self))

    def state_of(self, component: str) -> ComponentState | None:
        return self.states.get(component)


class _StateHandler:
    def __init__(self, lifecycle: LifecycleManager, label: str, state: ComponentState) -> None:
        self.lifecycle = lifecycle
        self.label = label
        self.state = state

    async def handle(self, event: Event) -> Any:
        self.lifecycle.states[event.source] = self.state
        print(f"[Lifecycle] {self.label}: {event.source} -> {event.dest} payload={event.payload!r}")
        return {"ok": True, "event": self.label, "state": self.state.name}


class _ErrorHandler:
    def __init__(self, lifecycle: LifecycleManager) -> None:
        self.lifecycle = lifecycle

    async def handle(self, event: Event) -> Any:
        self.lifecycle.states[event.source] = ComponentState.ERROR
        self.lifecycle.errors[event.source] = event.payload
        print(f"[Lifecycle] ERROR: {event.source} -> {event.dest} payload={event.payload!r}")
        return {"ok": False, "event": "ERROR", "state": ComponentState.ERROR.name, "payload": event.payload}


class _TickHandler:
    def __init__(self, lifecycle: LifecycleManager) -> None:
        self.lifecycle = lifecycle

    async def handle(self, event: Event) -> Any:
        self.lifecycle.states[event.source] = ComponentState.RUNNING
        print(f"[Tick] {event.source}: {event.payload!r}")
        return {"ok": True, "handled": "TICK", "payload": event.payload}
