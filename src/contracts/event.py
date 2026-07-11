from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from types import MappingProxyType
from typing import Any


class EventType(Enum):
    """Types d'événements connus du micro-kernel."""

    # Cycle de vie
    LOAD = auto()
    START = auto()
    TICK = auto()
    STOP = auto()
    ERROR = auto()

    # Contexte global
    CONTEXT_REQUEST = auto()
    CONTEXT_REPLY = auto()

    # Inférence
    INFERENCE_REQUEST = auto()
    INFERENCE_RESULT = auto()

    # SourceCandidate local — Phase 6.1-r1 live path
    SOURCE_CANDIDATE_INTAKE = auto()
    SOURCE_CANDIDATE_INTAKE_RESULT = auto()
    SOURCE_CANDIDATE_REVIEW = auto()
    SOURCE_CANDIDATE_REVIEW_RESULT = auto()
    SOURCE_CANDIDATE_DECISION = auto()
    SOURCE_CANDIDATE_DECISION_RESULT = auto()

    # Laboratoire spécialiste — Phase 0274-r1 live Scheduler binding
    LABORATORY_VISIT_REQUEST = auto()
    LABORATORY_VISIT_RESULT = auto()

    # Politique kernel
    POLICY_DENIED = auto()

    # Système
    SHUTDOWN = auto()


@dataclass(frozen=True, slots=True)
class Request:
    """Canal de réponse optionnel pour un Event.

    Le Future reste explicitement séparé du payload. Le payload conserve le sens
    métier de l'événement, tandis que Request décrit uniquement la mécanique de
    réponse coopérative.
    """

    reply: asyncio.Future[Any] | None = field(
        default=None,
        repr=False,
        compare=False,
    )
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
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    timestamp_ns: int = field(default_factory=time.monotonic_ns)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def with_request(self, request: Request) -> Event:
        """Retourne une copie de l'événement avec un canal de réponse."""

        return replace(self, request=request)

    def with_source(self, source: str) -> Event:
        """Retourne une copie de l'événement avec une nouvelle source."""

        return replace(self, source=source)
