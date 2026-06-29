from __future__ import annotations

import asyncio
from collections.abc import Sequence
from contextlib import suppress
from types import MappingProxyType
from typing import Any

from contracts.event import Event
from contracts.replay import EventLogSnapshot, EventRecord
from kernel.event_bus import EventBus


class EventRecorder:
    """Enregistreur passif d'événements pour audit et futur replay.

    Le recorder s'abonne à l'EventBus. Il ne publie rien, ne modifie aucune
    queue d'exécution et ne commande jamais le Scheduler. Il produit seulement
    des copies immuables des événements observés.
    """

    def __init__(self, event_bus: EventBus, max_records: int = 10_000) -> None:
        if max_records <= 0:
            raise ValueError("max_records must be positive")

        self._queue = event_bus.subscribe(None)
        self._max_records = max_records
        self._records: list[EventRecord] = []
        self._task: asyncio.Task[None] | None = None
        self._changed = asyncio.Event()

    @property
    def running(self) -> bool:
        """Indique si la tâche de collecte est active."""

        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        """Démarre la tâche passive de collecte."""

        if self.running:
            return

        self._task = asyncio.create_task(
            self._run(),
            name="missipy-event-recorder",
        )

    async def stop(self) -> None:
        """Arrête proprement la tâche de collecte."""

        if self._task is None:
            return

        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def wait_for_count(self, count: int, timeout: float = 1.0) -> None:
        """Attend qu'au moins ``count`` événements soient capturés."""

        if count < 0:
            raise ValueError("count must be non-negative")

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while len(self._records) < count:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError(f"expected {count} records, got {len(self._records)}")
            self._changed.clear()
            await asyncio.wait_for(self._changed.wait(), timeout=remaining)

    def snapshot(self) -> EventLogSnapshot:
        """Retourne une image immuable du journal courant."""

        return EventLogSnapshot(records=tuple(self._records))

    def records(self) -> Sequence[EventRecord]:
        """Vue séquentielle en lecture seule des événements capturés."""

        return self.snapshot().records

    async def _run(self) -> None:
        while True:
            event = await self._queue.get()
            self._append(event)
            self._queue.task_done()
            self._changed.set()

    def _append(self, event: Event) -> None:
        if len(self._records) >= self._max_records:
            del self._records[0]

        self._records.append(self._to_record(event))

    @staticmethod
    def _to_record(event: Event) -> EventRecord:
        metadata: dict[str, Any] = dict(event.metadata)
        return EventRecord(
            id=event.id,
            type=event.type.name,
            source=event.source,
            dest=event.dest,
            priority=event.priority,
            timestamp_ns=event.timestamp_ns,
            correlation_id=event.correlation_id,
            payload_repr=repr(event.payload),
            metadata=MappingProxyType(metadata),
        )
