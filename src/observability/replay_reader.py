from __future__ import annotations

from collections.abc import Iterable
from types import MappingProxyType
from typing import Any

from contracts.replay import EventLogSnapshot, EventRecord, ReplayEvent, ReplayPlan


class ReplayReader:
    """Lecteur passif d'un EventLogSnapshot.

    Le ReplayReader ne publie aucun événement et ne connaît pas le Scheduler. Il
    prépare uniquement des vues filtrées et des ReplayPlan immuables à partir du
    journal capturé par EventRecorder.
    """

    def __init__(self, snapshot: EventLogSnapshot) -> None:
        self._snapshot = snapshot

    @property
    def snapshot(self) -> EventLogSnapshot:
        """Snapshot source utilisé par le lecteur."""

        return self._snapshot

    def records(
        self,
        *,
        event_type: str | None = None,
        source: str | None = None,
        dest: str | None = None,
    ) -> tuple[EventRecord, ...]:
        """Retourne les records filtrés, sans modifier le snapshot source."""

        return tuple(
            record
            for record in self._snapshot.records
            if self._match(record, event_type=event_type, source=source, dest=dest)
        )

    def event_types(self) -> tuple[str, ...]:
        """Retourne les types d'événements distincts dans l'ordre d'apparition."""

        seen: set[str] = set()
        ordered: list[str] = []
        for record in self._snapshot.records:
            if record.type in seen:
                continue
            seen.add(record.type)
            ordered.append(record.type)
        return tuple(ordered)

    def to_replay_plan(
        self,
        *,
        include_types: Iterable[str] | None = None,
        exclude_types: Iterable[str] | None = None,
        source: str | None = None,
        dest: str | None = None,
    ) -> ReplayPlan:
        """Construit un ReplayPlan contrôlé à partir du snapshot.

        ``include_types`` restreint explicitement les types conservés.
        ``exclude_types`` retire certains types même s'ils sont inclus.
        Aucun payload vivant n'est reconstruit : seul ``payload_repr`` est
        propagé pour audit et futur moteur de replay déterministe.
        """

        include = set(include_types) if include_types is not None else None
        exclude = set(exclude_types) if exclude_types is not None else set()
        events: list[ReplayEvent] = []

        for record in self._snapshot.records:
            if include is not None and record.type not in include:
                continue
            if record.type in exclude:
                continue
            if not self._match(record, event_type=None, source=source, dest=dest):
                continue
            events.append(self._to_replay_event(record))

        return ReplayPlan(
            events=tuple(events),
            source_record_count=self._snapshot.count,
        )

    @staticmethod
    def _match(
        record: EventRecord,
        *,
        event_type: str | None,
        source: str | None,
        dest: str | None,
    ) -> bool:
        if event_type is not None and record.type != event_type:
            return False
        if source is not None and record.source != source:
            return False
        if dest is not None and record.dest != dest:
            return False
        return True

    @staticmethod
    def _to_replay_event(record: EventRecord) -> ReplayEvent:
        metadata: dict[str, Any] = dict(record.metadata)
        return ReplayEvent(
            original_id=record.id,
            type=record.type,
            source=record.source,
            dest=record.dest,
            priority=record.priority,
            timestamp_ns=record.timestamp_ns,
            correlation_id=record.correlation_id,
            payload_repr=record.payload_repr,
            metadata=MappingProxyType(metadata),
        )
