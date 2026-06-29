from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from .event import Event


class Component(ABC):
    """Contrat minimal d'un expert ou service piloté par MissiPy."""

    name: str

    @abstractmethod
    def tick(self) -> AsyncGenerator[Event, Any]:
        """Boucle coopérative principale.

        Le composant ne commande rien directement : il émet des intentions
        via `yield Event(...)` et reçoit éventuellement un résultat via `asend`.
        """
        raise NotImplementedError

    @abstractmethod
    async def context(self) -> dict[str, Any]:
        """Retourne l'état observable du composant."""
        raise NotImplementedError
