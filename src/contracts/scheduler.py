from __future__ import annotations

from abc import ABC, abstractmethod

from .event import Event


class SchedulerContract(ABC):
    @abstractmethod
    async def emit(self, event: Event) -> None:
        """Réceptionne un événement produit par un proxy ou le kernel."""
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """Demande l'arrêt propre du scheduler."""
        raise NotImplementedError
