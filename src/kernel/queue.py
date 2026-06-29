from __future__ import annotations

import asyncio
import itertools
from typing import Iterator

from contracts.event import Event


class PriorityQueue:
    """File de priorité déterministe.

    Deux événements de même priorité gardent leur ordre d'insertion grâce au
    compteur monotone interne.
    """

    def __init__(self) -> None:
        self._seq: Iterator[int] = itertools.count()
        self._queue: asyncio.PriorityQueue[tuple[int, int, Event]] = (
            asyncio.PriorityQueue()
        )

    async def put(self, priority: int, event: Event) -> None:
        await self._queue.put((priority, next(self._seq), event))

    async def get(self) -> tuple[int, Event]:
        priority, _seq, event = await self._queue.get()
        return priority, event

    def task_done(self) -> None:
        self._queue.task_done()

    def qsize(self) -> int:
        """Nombre courant d'événements en attente."""

        return self._queue.qsize()

    async def join(self) -> None:
        await self._queue.join()
