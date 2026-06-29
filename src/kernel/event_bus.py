from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import DefaultDict

from contracts.event import Event, EventType


class EventBus:
    """Bus d'observation.

    L'EventBus ne commande jamais l'exécution. Il permet uniquement aux outils
    d'observabilité, de métriques ou de replay de recevoir une copie des
    événements publiés par le Dispatcher ou les services du kernel.
    """

    def __init__(self) -> None:
        self._subscribers: DefaultDict[EventType | None, list[asyncio.Queue[Event]]] = (
            defaultdict(list)
        )

    def subscribe(self, event_type: EventType | None = None) -> asyncio.Queue[Event]:
        """Retourne une queue d'observation pour un type d'événement."""

        queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers[event_type].append(queue)
        return queue

    async def publish(self, event: Event) -> None:
        """Publie une copie observable d'un événement."""

        for queue in self._subscribers.get(None, []):
            await queue.put(event)

        for queue in self._subscribers.get(event.type, []):
            await queue.put(event)
