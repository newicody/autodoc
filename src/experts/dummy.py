#  experts/dummy.py

from contracts.component import Component
from contracts.event import Event, EventType
from typing import AsyncGenerator, Any

class DummyExpert(Component):
    name = "DummyExpert"

    def tick(self) -> AsyncGenerator[Event, Any]:
        # Exemple simple : émet un événement de type TICK
        yield Event(EventType.TICK, source=self.name, payload="hello")
        # On ne boucle pas ici pour simplifier, le STOP sera émis à la fin du générateur

    async def context(self) -> dict:
        return {"status": "idle", "counter": 0}

# Instance unique chargée par le loader
component = DummyExpert()
