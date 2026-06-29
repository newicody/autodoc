# contracts/component.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any
from .event import Event

class Component(ABC):
    """Contrat minimal : chaque expert / service implémente ces deux méthodes."""
    @abstractmethod
    def tick(self) -> AsyncGenerator[Event, Any]:
        """Coroutine principale, émet des intentions via yield Event(...)."""
        ...

    @abstractmethod
    async def context(self) -> dict:
        """Retourne l'état actuel du composant pour le Context Engine."""
        ...
