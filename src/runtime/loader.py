from __future__ import annotations

import importlib
from pathlib import Path

from contracts.component import Component


def load_components() -> list[Component]:
    """Charge les composants concrets depuis le dossier experts/."""

    experts_dir = Path(__file__).parent.parent / "experts"
    components: list[Component] = []

    for file_path in sorted(experts_dir.glob("*.py")):
        if file_path.name == "__init__.py":
            continue

        module = importlib.import_module(f"experts.{file_path.stem}")
        component = getattr(module, "component", None)
        if isinstance(component, Component):
            components.append(component)

    return components
