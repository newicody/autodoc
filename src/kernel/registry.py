from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.component import ComponentProxy


class Registry:
    """Registre unique des ComponentProxy actifs."""

    def __init__(self) -> None:
        self._components: dict[str, ComponentProxy] = {}

    def register(self, name: str, proxy: ComponentProxy) -> None:
        self._components[name] = proxy

    def get(self, name: str) -> ComponentProxy:
        return self._components[name]

    def all(self) -> Mapping[str, ComponentProxy]:
        return self._components.copy()
