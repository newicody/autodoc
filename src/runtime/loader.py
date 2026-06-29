from __future__ import annotations

import importlib
import pathlib

from contracts.component import Component


def load_components() -> list[Component]:
    """Charge les composants exposant une variable `component` dans experts/*.py."""

    experts_dir = pathlib.Path(__file__).parent.parent / "experts"
    components: list[Component] = []

    for path in sorted(experts_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        module = importlib.import_module(f"experts.{path.stem}")
        component = getattr(module, "component", None)
        if component is not None:
            components.append(component)

    return components
