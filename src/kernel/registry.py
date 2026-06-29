# kernel/registry.py
from typing import Dict
from runtime.component import ComponentProxy

class Registry:
    def __init__(self):
        self._components: Dict[str, ComponentProxy] = {}

    def register(self, name: str, proxy: ComponentProxy):
        self._components[name] = proxy

    def get(self, name: str) -> ComponentProxy:
        return self._components[name]

    def all(self):
        return self._components.copy()
