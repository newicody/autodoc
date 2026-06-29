from __future__ import annotations

from abc import ABC, abstractmethod

from .event import Event


class SchedulerContract(ABC):
    """Surface minimale exposée aux ComponentProxy."""

    @abstractmethod
    async def emit(self, event: Event) -> None:
        """Réceptionne un événement émis par un proxy."""

        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """Demande un arrêt coopératif du kernel."""

        raise NotImplementedError
