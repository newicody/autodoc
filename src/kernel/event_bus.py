from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import DefaultDict

from contracts.event import Event, EventType


class EventBus:
    """Bus d'observation.

    Important : le bus ne commande pas l'exécution. Le chemin critique reste
    Scheduler -> PriorityQueue -> Dispatcher -> Handler.
    """

    def __init__(self) -> None:
        self._subscribers: DefaultDict[EventType | None, list[asyncio.Queue[Event]]] = defaultdict(list)

    def subscribe(self, event_type: EventType | None = None) -> asyncio.Queue[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers[event_type].append(queue)
        return queue

    async def publish(self, event: Event) -> None:
        for queue in self._subscribers.get(None, []):
            await queue.put(event)
        for queue in self._subscribers.get(event.type, []):
            await queue.put(event)
