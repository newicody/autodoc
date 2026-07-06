#!/usr/bin/env python3
"""Qdrant projection live-smoke planner through the existing adapter surface.

0139 deliberately does not introduce a new Qdrant adapter.  It inventories the
existing projection membrane and prepares the operator smoke.  Execution is
strictly opt-in with --execute.  The tool does not import qdrant_client or touch
Scheduler/RouteProxy; it only inspects and, when an executable adapter entrypoint
already exists, delegates to that existing entrypoint.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Sequence

DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"
DEFAULT_COLLECTION = "autodoc_smoke_e5_384"
DEFAULT_DIMENSION = 384
DEFAULT_SQL_REF = "sql:smoke/vector-indexing/0139"
DEFAULT_PAYLOAD_TEXT = "passage: Qdrant stores vector projections and sql_ref payloads; SQL remains durable authority."
KNOWN_EXECUTABLE_ENTRYPOINTS = (
    "run_qdrant_projection_live_smoke",
    "run_projection_live_smoke",
    "run_qdrant_smoke",
    "qdrant_projection_live_smoke",
)


@dataclass(frozen=True, slots=True)
class QdrantSmokeSurface:
    key: str
    path: Path
    reason: str

    def to_mapping(self, *, root: Path) -> dict[str, str]:
        return {
            "key": self.key,
            "status": "present" if self.path.exists() else "missing",
            "path": _display_path(self.path, root=root),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class QdrantAdapterInventory:
    adapter_path: Path
    functions: tuple[str, ...]
    classes: tuple[str, ...]
    imports: tuple[str, ...]

    @property
    def executable_entrypoints(self) -> tuple[str, ...]:
        return tuple(name for name in KNOWN_EXECUTABLE_ENTRYPOINTS if name in self.functions)

    @property
    def imports_qdrant_client(self) -> bool:
        return any(name in {"qdrant_client", "qdrant"} for name in self.imports)


@dataclass(frozen=True, slots=True)
class QdrantProjectionSmokePlan:
    repository_root: Path
    qdrant_url: str
    collection: str
    dimension: int
    sql_ref: str
    execute: bool
    surfaces: tuple[QdrantSmokeSurface, ...]
    adapter_inventory: QdrantAdapterInventory | None

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces)

    def missing_surfaces(self) -> tuple[QdrantSmokeSurface, ...]:
        return tuple(surface for surface in self.surfaces if not surface.path.exists())

    def to_markdown(self) -> str:
        lines = [
            "# Qdrant projection live smoke plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"qdrant_url: `{self.qdrant_url}`",
            f"collection: `{self.collection}`",
            f"dimension: `{self.dimension}`",
            f"sql_ref: `{self.sql_ref}`",
            f"ready_for_qdrant_projection_smoke: `{str(self.ready).lower()}`",
            f"execute: `{str(self.execute).lower()}`",
            "",
            "## Existing surfaces",
            "",
            "| key | status | path | reason |",
            "| --- | --- | --- | --- |",
        ]
        for surface in self.surfaces:
            row = surface.to_mapping(root=self.repository_root)
            lines.append(f"| {row['key']} | {row['status']} | `{row['path']}` | {row['reason']} |")
        lines.extend(["", "## Existing adapter inventory", ""])
        if self.adapter_inventory is None:
            lines.append("adapter_inventory: `unavailable`")
        else:
            inventory = self.adapter_inventory
            lines.append(f"adapter_path: `{_display_path(inventory.adapter_path, root=self.repository_root)}`")
            lines.append(f"functions: `{', '.join(inventory.functions) or 'none'}`")
            lines.append(f"classes: `{', '.join(inventory.classes) or 'none'}`")
            lines.append(f"executable_entrypoints: `{', '.join(inventory.executable_entrypoints) or 'none'}`")
            lines.append(f"adapter_imports_qdrant_client: `{str(inventory.imports_qdrant_client).lower()}`")
        lines.extend([
            "",
            "## Smoke payload",
            "",
            "```text",
            f"collection={self.collection}",
            f"dimension={self.dimension}",
            f"sql_ref={self.sql_ref}",
            f"text={DEFAULT_PAYLOAD_TEXT}",
            "vector=[deterministic 384-dim smoke vector]",
            "```",
            "",
            "## Boundary",
            "",
            "- reuses src/inference/qdrant_projection_adapter.py as existing Qdrant projection membrane",
            "- reuses src/context/vector_collection_registry.py as collection registry",
            "- reuses src/context/vector_indexing_job_plan.py as projection job contract",
            "- does not create VectorQdrantProjectionAdapter",
            "- does not import Qdrant from Scheduler, RouteProxy, PolicyEngine, Dispatcher, or context contracts",
            "- Qdrant stores projection/recall indexes, not durable truth",
            "- dry-run is the default; --execute is required for backend execution",
        ])
        return "\n".join(lines) + "\n"


def build_qdrant_projection_smoke_plan(
    root: Path,
    *,
    qdrant_url: str,
    collection: str,
    dimension: int,
    sql_ref: str,
    execute: bool,
) -> QdrantProjectionSmokePlan:
    root = root.resolve()
    adapter_path = root / "src" / "inference" / "qdrant_projection_adapter.py"
    surfaces = (
        QdrantSmokeSurface(
            key="qdrant_projection_adapter",
            path=adapter_path,
            reason="existing Qdrant projection membrane",
        ),
        QdrantSmokeSurface(
            key="vector_collection_registry",
            path=root / "src" / "context" / "vector_collection_registry.py",
            reason="existing vector collection registry",
        ),
        QdrantSmokeSurface(
            key="vector_indexing_job_plan",
            path=root / "src" / "context" / "vector_indexing_job_plan.py",
            reason="existing VectorProjectionJob contract",
        ),
    )
    inventory = inspect_qdrant_adapter(adapter_path) if adapter_path.exists() else None
    return QdrantProjectionSmokePlan(
        repository_root=root,
        qdrant_url=qdrant_url,
        collection=collection,
        dimension=dimension,
        sql_ref=sql_ref,
        execute=execute,
        surfaces=surfaces,
        adapter_inventory=inventory,
    )


def inspect_qdrant_adapter(adapter_path: Path) -> QdrantAdapterInventory:
    tree = ast.parse(adapter_path.read_text(encoding="utf-8"))
    functions: list[str] = []
    classes: list[str] = []
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    return QdrantAdapterInventory(
        adapter_path=adapter_path,
        functions=tuple(sorted(functions)),
        classes=tuple(sorted(classes)),
        imports=tuple(sorted(imports)),
    )


def run_existing_entrypoint(plan: QdrantProjectionSmokePlan) -> int:
    if not plan.ready:
        for surface in plan.missing_surfaces():
            print(f"missing surface: {surface.key} -> {surface.path}", file=sys.stderr)
        return 2
    if plan.adapter_inventory is None or not plan.adapter_inventory.executable_entrypoints:
        print(
            "no executable Qdrant smoke entrypoint found in existing adapter; "
            "next step should extend src/inference/qdrant_projection_adapter.py rather than creating a new adapter",
            file=sys.stderr,
        )
        return 4
    entrypoint = plan.adapter_inventory.executable_entrypoints[0]
    code = "\n".join([
        "from inference import qdrant_projection_adapter as adapter",
        f"fn = getattr(adapter, {entrypoint!r})",
        "kwargs = {",
        f"    'qdrant_url': {plan.qdrant_url!r},",
        f"    'collection': {plan.collection!r},",
        f"    'dimension': {plan.dimension!r},",
        f"    'sql_ref': {plan.sql_ref!r},",
        "}",
        "try:",
        "    result = fn(**kwargs)",
        "except TypeError:",
        "    result = fn()",
        "print(result)",
    ])
    completed = subprocess.run(
        (sys.executable, "-c", code),
        cwd=plan.repository_root,
        env=None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan or run Qdrant projection smoke through existing repo surfaces.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION)
    parser.add_argument("--sql-ref", default=DEFAULT_SQL_REF)
    parser.add_argument("--format", choices=("markdown", "jsonish"), default="markdown")
    parser.add_argument("--execute", action="store_true", help="Delegate to an existing adapter smoke entrypoint if one exists")
    args = parser.parse_args(argv)

    plan = build_qdrant_projection_smoke_plan(
        Path(args.root),
        qdrant_url=args.qdrant_url,
        collection=args.collection,
        dimension=args.dimension,
        sql_ref=args.sql_ref,
        execute=bool(args.execute),
    )
    if args.format == "markdown":
        print(plan.to_markdown(), end="")
    else:
        print({
            "ready": plan.ready,
            "qdrant_url": plan.qdrant_url,
            "collection": plan.collection,
            "dimension": plan.dimension,
            "sql_ref": plan.sql_ref,
        })
    if args.execute:
        return run_existing_entrypoint(plan)
    return 0 if plan.ready else 2


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
