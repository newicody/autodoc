# contracts/event.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional

class EventType(Enum):
    # Cycle de vie
    LOAD = auto()
    START = auto()
    TICK = auto()
    STOP = auto()
    ERROR = auto()
    # Scheduler
    CONTEXT_REQUEST = auto()
    CONTEXT_REPLY = auto()
    # Système
    SHUTDOWN = auto()

@dataclass(frozen=True)
class Event:
    type: EventType
    source: str
    dest: str = "scheduler"
    payload: Any = None
    priority: int = 0
    correlation_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(id(object())))  # unique simple
