from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
INTERNAL_ROOTS = {
    "visualization",
    "context",
    "contracts",
    "experts",
    "inference",
    "kernel",
    "observability",
    "policy",
    "runtime",
}
STD_LIB = set(sys.stdlib_module_names) | {"__future__"}
OPTIONAL_EXTERNAL_IMPORT_SITES: dict[str, set[str]] = {
    # OpenVINO integration is allowed only in the explicit runtime module.
    # The contract/backend layers must keep working without importing openvino.
    "openvino": {"src/inference/openvino_runtime.py"},
    # NumPy is only used as an optional adapter at the OpenVINO boundary.
    "numpy": {"src/inference/openvino_runtime.py"},
    # Transformers is imported lazily only by the explicit tokenizer adapter.
    "transformers": {"src/inference/transformers_tokenizer.py"},
}


def python_sources() -> list[Path]:
    return sorted(
        p
        for p in SRC.rglob("*.py")
        if "__pycache__" not in p.parts
    )


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def imported_roots(tree: ast.Module) -> list[str]:
    roots: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.level == 0:
                roots.append(node.module.split(".", 1)[0])
    return roots


def test_stdlib_first_no_unapproved_external_imports() -> None:
    errors: list[str] = []

    for path in python_sources():
        rel = relative(path)
        for root in imported_roots(parse(path)):
            if root in STD_LIB or root in INTERNAL_ROOTS:
                continue
            allowed_sites = OPTIONAL_EXTERNAL_IMPORT_SITES.get(root, set())
            if rel not in allowed_sites:
                errors.append(f"{rel}: unapproved external import {root!r}")

    assert errors == []


def test_contract_dataclasses_are_frozen() -> None:
    errors: list[str] = []

    for path in sorted((SRC / "contracts").rglob("*.py")):
        tree = parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for decorator in node.decorator_list:
                is_dataclass = False
                frozen = False
                if isinstance(decorator, ast.Call) and getattr(decorator.func, "id", None) == "dataclass":
                    is_dataclass = True
                    for keyword in decorator.keywords:
                        if keyword.arg == "frozen" and isinstance(keyword.value, ast.Constant):
                            frozen = keyword.value.value is True
                elif getattr(decorator, "id", None) == "dataclass":
                    is_dataclass = True

                if is_dataclass and not frozen:
                    errors.append(f"{relative(path)}:{node.name} dataclass must be frozen")

    assert errors == []


def test_scheduler_has_no_domain_backend_imports() -> None:
    scheduler = SRC / "kernel" / "scheduler.py"
    imported = set(imported_roots(parse(scheduler)))
    forbidden = {
        "experts",
        "inference",
        "observability",
        "qdrant",
        "sqlite",
        "storage",
        "runtime",
    }
    assert sorted(imported & forbidden) == []


def test_openvino_runtime_is_not_imported_before_runtime_phase() -> None:
    errors: list[str] = []

    for path in python_sources():
        rel = relative(path)
        for root in imported_roots(parse(path)):
            if root != "openvino":
                continue
            if rel not in OPTIONAL_EXTERNAL_IMPORT_SITES["openvino"]:
                errors.append(f"{rel}: openvino import must stay isolated in explicit runtime module")

    assert errors == []
