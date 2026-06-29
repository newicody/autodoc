from __future__ import annotations

from typing import Any

from contracts.event import Event
from kernel.registry import Registry


class ContextRequestHandler:
    """Handler kernel d'une requête de contexte.

    C'est le seul endroit du chemin événementiel qui touche explicitement le
    ComponentProxy pour lire le contexte du composant réel.
    """

    def __init__(self, registry: Registry) -> None:
        self.registry = registry

    async def handle(self, event: Event) -> dict[str, Any]:
        proxy = self.registry.get(event.dest)
        context = await proxy.context()
        return {
            "ok": True,
            "component": event.dest,
            "context": context,
        }
