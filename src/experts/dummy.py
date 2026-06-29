from __future__ import annotations

from typing import Any, AsyncGenerator

from contracts.component import Component
from contracts.event import Event, EventType


class DummyExpert(Component):
    name = "DummyExpert"

    def __init__(self) -> None:
        self.counter = 0
        self.last_result: Any = None

    async def tick(self) -> AsyncGenerator[Event, Any]:
        self.last_result = yield Event(EventType.TICK, source=self.name, payload="hello")
        self.counter += 1

    async def context(self) -> dict[str, Any]:
        return {
            "status": "idle",
            "counter": self.counter,
            "last_result": self.last_result,
        }


component = DummyExpert()
