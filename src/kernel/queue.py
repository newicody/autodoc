# kernel/queue.py
import asyncio
import itertools
from contracts.event import Event

class PriorityQueue:
    def __init__(self):
        self._seq = itertools.count()
        self._queue = asyncio.PriorityQueue()

    async def put(self, priority: int, event: Event):
        await self._queue.put((priority, next(self._seq), event))

    async def get(self) -> tuple[int, Event]:
        priority, _, event = await self._queue.get()
        return priority, event
