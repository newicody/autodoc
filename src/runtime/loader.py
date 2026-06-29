# runtime/loader.py
import importlib
import pathlib
from contracts.component import Component

def load_components() -> list[Component]:
    """Charge tous les composants concrets depuis le dossier experts/."""
    experts_dir = pathlib.Path(__file__).parent.parent / "experts"
    components = []
    for f in experts_dir.glob("*.py"):
        if f.name == "__init__.py":
            continue
        mod = importlib.import_module(f"experts.{f.stem}")
        # On suppose que chaque module expose une variable `component` instance de Component
        if hasattr(mod, "component"):
            components.append(mod.component)
    return components
