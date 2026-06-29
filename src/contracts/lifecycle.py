from __future__ import annotations

from enum import Enum, auto


class ComponentState(Enum):
    """État observable minimal d'un composant piloté par le kernel."""

    CREATED = auto()
    LOADED = auto()
    STARTED = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()
