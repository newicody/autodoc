from __future__ import annotations

import asyncio
import itertools

from contracts.event import Event


class PriorityQueue:
    """File prioritaire déterministe.

    `_seq` évite de comparer deux Event quand ils ont la même priorité.
    """

    def __init__(self) -> None:
        self._seq = itertools.count()
        self._queue: asyncio.PriorityQueue[tuple[int, int, Event]] = asyncio.PriorityQueue()

    async def put(self, priority: int, event: Event) -> None:
        await self._queue.put((priority, next(self._seq), event))

    async def get(self) -> tuple[int, Event]:
        priority, _, event = await self._queue.get()
        return priority, event

    def task_done(self) -> None:
        self._queue.task_done()
