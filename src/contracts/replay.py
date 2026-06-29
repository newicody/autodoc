from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class EventRecord:
    """Copie immuable et rejouable d'un événement observé.

    Un EventRecord ne transporte jamais le canal ``Request.reply``. Les Future
    asyncio restent une mécanique vivante du kernel et ne sont pas sérialisables.
    Le recorder capture donc uniquement les champs nécessaires à l'audit, au
    debug et au futur replay déterministe.
    """

    id: str
    type: str
    source: str
    dest: str
    priority: int
    timestamp_ns: int
    correlation_id: str | None = None
    payload_repr: str = ""
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class EventLogSnapshot:
    """Image immuable du journal d'événements observé."""

    records: tuple[EventRecord, ...]

    @property
    def count(self) -> int:
        """Nombre d'événements capturés."""

        return len(self.records)

    @property
    def last_event_type(self) -> str | None:
        """Type du dernier événement capturé, s'il existe."""

        if not self.records:
            return None
        return self.records[-1].type
