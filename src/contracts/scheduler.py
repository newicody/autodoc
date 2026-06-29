# contracts/scheduler.py
from __future__ import annotations
from abc import ABC, abstractmethod
from .event import Event

class SchedulerContract(ABC):
    @abstractmethod
    async def emit(self, event: Event) -> None:
        """Réceptionne un événement d’un composant (via son proxy)."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        ...
