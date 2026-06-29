from __future__ import annotations

from typing import Any, AsyncGenerator

from contracts.component import Component
from contracts.event import Event, EventType


class DummyExpert(Component):
    """Composant de test minimal du micro-kernel."""

    name = "DummyExpert"

    async def tick(self) -> AsyncGenerator[Event, Any]:
        result = yield Event(EventType.TICK, source=self.name, payload="hello")
        _ = result

    async def context(self) -> dict[str, Any]:
        return {"status": "idle", "counter": 0}


component = DummyExpert()
