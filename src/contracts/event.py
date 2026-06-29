from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from typing import Any, Mapping


class EventType(Enum):
    """Types d'événements connus du micro-kernel Phase 1."""

    # Cycle de vie
    LOAD = auto()
    START = auto()
    TICK = auto()
    STOP = auto()
    ERROR = auto()

    # Contexte global
    CONTEXT_REQUEST = auto()
    CONTEXT_REPLY = auto()

    # Inférence future
    INFERENCE_REQUEST = auto()
    INFERENCE_RESULT = auto()

    # Système
    SHUTDOWN = auto()


@dataclass(slots=True)
class Request:
    """Canal de réponse optionnel pour un Event.

    Phase 1 : le Future reste local au processus Python.
    Phase cible : ce champ pourra être remplacé par reply_to/correlation_id
    pour du multi-processus ou du replay déterministe.
    """

    reply: asyncio.Future[Any] | None = field(default=None, repr=False, compare=False)
    timeout: float = 5.0


@dataclass(frozen=True, slots=True)
class Event:
    """Message immuable circulant dans le kernel."""

    type: EventType
    source: str
    dest: str = "scheduler"
    payload: Any = None
    priority: int = 0
    correlation_id: str | None = None
    request: Request | None = field(default=None, compare=False)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    timestamp_ns: int = field(default_factory=time.monotonic_ns)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def with_request(self, request: Request) -> "Event":
        return replace(self, request=request)

    def with_source(self, source: str) -> "Event":
        return replace(self, source=source)
