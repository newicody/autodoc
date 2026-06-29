from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from .event import Event


class Component(ABC):
    """Contrat minimal d'un expert ou service piloté par MissiPy."""

    name: str

    @abstractmethod
    async def tick(self) -> AsyncGenerator[Event, Any]:
        """Boucle coopérative principale.

        Un composant n'appelle pas directement une action. Il émet une intention
        via ``yield Event(...)`` et reçoit éventuellement une réponse via
        ``asend(result)``.
        """

        raise NotImplementedError

    @abstractmethod
    async def context(self) -> dict[str, Any]:
        """Retourne l'état observable du composant."""

        raise NotImplementedError
