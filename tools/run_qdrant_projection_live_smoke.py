#!/usr/bin/env python3
"""Qdrant projection live-smoke planner through the existing adapter surface.

0139 introduced a dry-run planner.  0140 keeps the same operator surface and
adds an opt-in live REST smoke executor that reuses the existing
``src/inference/qdrant_projection_adapter.py`` membrane and its injected
executor protocol.  This file is an operator smoke tool, not a new adapter; it
keeps Scheduler, RouteProxy, PolicyEngine, Dispatcher, and context contracts
outside Qdrant.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Sequence

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
            "- 0140 uses the existing QdrantProjectionExecutor injection seam instead of a new adapter",
            "- operator REST execution lives in tools/run_qdrant_projection_live_smoke.py only",
            "- HTTP 409 while ensuring a collection is treated as idempotent collection-already-exists",
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
    if plan.adapter_inventory is not None and plan.adapter_inventory.executable_entrypoints:
        return _delegate_to_adapter_entrypoint(plan)
    return run_operator_rest_smoke(plan)


def run_operator_rest_smoke(plan: QdrantProjectionSmokePlan) -> int:
    """Run a live Qdrant smoke through existing projection contracts.

    This function is intentionally an operator smoke executor.  It uses the
    existing adapter's data contracts and injected-executor seam, while the
    REST calls remain in ``tools/`` so no Scheduler/RouteProxy/context contract
    imports Qdrant.
    """

    try:
        point = build_smoke_projection_point(plan)
        rest_point = qdrant_rest_point_from_projection(point)
        put_collection = qdrant_put_collection_payload(plan.dimension)
        upsert_payload = {"points": [rest_point]}
        search_payload = qdrant_search_payload(point.vector, limit=1)

        _qdrant_request(
            "PUT",
            _qdrant_url(plan, f"/collections/{plan.collection}"),
            put_collection,
            allow_http_statuses=(409,),
        )
        _qdrant_request("PUT", _qdrant_url(plan, f"/collections/{plan.collection}/points?wait=true"), upsert_payload)
        search_response = _qdrant_request(
            "POST",
            _qdrant_url(plan, f"/collections/{plan.collection}/points/search"),
            search_payload,
        )
    except (ImportError, RuntimeError, urllib.error.URLError, TimeoutError) as exc:
        print(f"qdrant live smoke failed: {exc}", file=sys.stderr)
        return 5

    print("# Qdrant projection live smoke result")
    print("")
    print(f"collection: `{plan.collection}`")
    print(f"dimension: `{plan.dimension}`")
    print(f"sql_ref: `{point.sql_context_ref}`")
    print(f"point_id: `{point.point_id}`")
    print(f"qdrant_rest_id: `{rest_point['id']}`")
    print("upsert_acknowledged: `true`")
    print(f"search_result_keys: `{', '.join(sorted(search_response.keys()))}`")
    print("boundary: `existing qdrant_projection_adapter contracts + operator REST executor`")
    return 0


def build_smoke_projection_point(plan: QdrantProjectionSmokePlan):
    _prepend_src(plan.repository_root)
    from inference.openvino_embedding_adapter import (  # type: ignore[import-not-found]
        OpenVINOEmbeddingPolicy,
        OpenVINOEmbeddingRuntimeTarget,
        OpenVINOEmbeddingText,
        build_embedding_vector,
    )
    from inference.qdrant_projection_adapter import (  # type: ignore[import-not-found]
        QdrantProjectionPolicy,
        local_qdrant_projection_target,
        build_qdrant_projection_point,
    )

    target = OpenVINOEmbeddingRuntimeTarget(dimension=plan.dimension)
    policy = OpenVINOEmbeddingPolicy(expected_dimension=plan.dimension)
    text = OpenVINOEmbeddingText(
        source_ref=f"ctx-fragment:{plan.sql_ref}",
        text=DEFAULT_PAYLOAD_TEXT,
        role="passage",
        metadata=(
            ("context_ref", plan.sql_ref),
            ("smoke", "0140-qdrant-operator-rest"),
        ),
    )
    embedding = build_embedding_vector(text, deterministic_normalized_vector(plan.dimension), target, policy)
    projection_target = local_qdrant_projection_target(collection_name=plan.collection, vector_dimension=plan.dimension)
    return build_qdrant_projection_point(embedding, projection_target, QdrantProjectionPolicy())


def deterministic_normalized_vector(dimension: int) -> tuple[float, ...]:
    if dimension <= 0:
        raise ValueError("dimension must be > 0")
    value = 1.0 / (dimension ** 0.5)
    return tuple(value for _ in range(dimension))


def qdrant_put_collection_payload(dimension: int) -> dict[str, object]:
    if dimension <= 0:
        raise ValueError("dimension must be > 0")
    return {"vectors": {"size": dimension, "distance": "Cosine"}}


def qdrant_search_payload(vector: Sequence[float], *, limit: int) -> dict[str, object]:
    if limit <= 0:
        raise ValueError("limit must be > 0")
    return {"vector": list(vector), "limit": limit, "with_payload": True, "with_vector": False}


def qdrant_rest_point_from_projection(point: object) -> dict[str, object]:
    point_id = getattr(point, "point_id")
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, str(point_id))),
        "vector": list(getattr(point, "vector")),
        "payload": {
            **dict(getattr(point, "payload")),
            "typed_point_id": str(point_id),
            "sql_context_ref": str(getattr(point, "sql_context_ref")),
        },
    }


def _delegate_to_adapter_entrypoint(plan: QdrantProjectionSmokePlan) -> int:
    assert plan.adapter_inventory is not None
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


def _qdrant_request(
    method: str,
    url: str,
    payload: dict[str, object],
    *,
    timeout: float = 5.0,
    allow_http_statuses: tuple[int, ...] = (),
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - operator local smoke URL is explicit.
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code in allow_http_statuses:
            return {
                "status": "ok",
                "http_status": exc.code,
                "already_exists": True,
                "idempotent_conflict": True,
            }
        raise
    if not raw:
        return {}
    decoded = json.loads(raw)
    if not isinstance(decoded, dict):
        raise RuntimeError("Qdrant response must be a JSON object")
    status = decoded.get("status")
    if status not in (None, "ok"):
        raise RuntimeError(f"Qdrant returned non-ok status: {status!r}")
    return decoded


def _qdrant_url(plan: QdrantProjectionSmokePlan, path: str) -> str:
    base = plan.qdrant_url.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _prepend_src(root: Path) -> None:
    src = str((root / "src").resolve())
    if src not in sys.path:
        sys.path.insert(0, src)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan or run Qdrant projection smoke through existing repo surfaces.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION)
    parser.add_argument("--sql-ref", default=DEFAULT_SQL_REF)
    parser.add_argument("--format", choices=("markdown", "jsonish"), default="markdown")
    parser.add_argument("--execute", action="store_true", help="Run a live operator smoke through existing adapter contracts")
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
