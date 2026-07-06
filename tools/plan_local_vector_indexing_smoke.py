"""Read-only readiness plan for the local vector-indexing smoke test.

0137 intentionally does not create a runtime, adapter, daemon, or scheduler path.
It inventories existing surfaces so the first real smoke test can reuse the
current RouteProxy/Scheduler/OpenVINO/Qdrant/SQL components instead of creating
parallel wheels.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
from typing import Iterable, Sequence

EXPECTED_SURFACES: tuple[tuple[str, str, str], ...] = (
    ("route_proxy_runtime", "src/runtime/route_proxy_runtime_minimal.py", "0130 RouteProxy runtime root/frame IO"),
    ("scheduler_route_handler", "src/runtime/scheduler_route_handler_minimal.py", "0131/0133 existing scheduler route handler"),
    ("vector_indexing_plan", "src/context/vector_indexing_job_plan.py", "0128 vector indexing job contracts"),
    ("vector_collection_registry", "src/context/vector_collection_registry.py", "0127 existing vector collection registry"),
    ("openvino_embedding_membrane", "src/inference/openvino_embedding_adapter.py", "existing OpenVINO/E5 embedding membrane"),
    ("openvino_runtime_boundary", "src/inference/openvino_runtime.py", "single real OpenVINO import boundary"),
    ("qdrant_projection_adapter", "src/inference/qdrant_projection_adapter.py", "existing Qdrant projection adapter"),
    ("sql_context_store", "src/context/sql_context_store.py", "durable context authority"),
)

NEXT_STEPS: tuple[str, ...] = (
    "stabilize 0136-r1 so Qdrant registry assertions match the real repository",
    "run this readiness inventory and verify all expected existing surfaces are found",
    "run OpenVINO/E5 smoke through the existing inference membrane only",
    "run Qdrant projection smoke through the existing Qdrant adapter only",
    "run local vector indexing smoke from text to embedding result to projection ack",
    "then wire Scheduler handler to enqueue the already-defined vector indexing job plan",
)

FORBIDDEN_NEW_WHEELS: tuple[str, ...] = (
    "VectorOpenVINOEmbeddingAdapter",
    "VectorQdrantProjectionAdapter",
    "LocalVectorIndexingOrchestrator",
    "SchedulerOpenVINORunner",
    "RouteProxyQdrantWorker",
)


@dataclass(frozen=True, slots=True)
class SurfaceReadiness:
    """One existing surface required before the local smoke test."""

    key: str
    path: str
    reason: str
    exists: bool

    def to_mapping(self) -> dict[str, object]:
        return {
            "key": self.key,
            "path": self.path,
            "reason": self.reason,
            "exists": self.exists,
        }


@dataclass(frozen=True, slots=True)
class LocalVectorIndexingSmokeReadiness:
    """Read-only smoke-test readiness report."""

    repository_root: str
    surfaces: tuple[SurfaceReadiness, ...]
    next_steps: tuple[str, ...]
    forbidden_new_wheels: tuple[str, ...]

    @property
    def ready_for_local_smoke(self) -> bool:
        return all(surface.exists for surface in self.surfaces)

    @property
    def missing_paths(self) -> tuple[str, ...]:
        return tuple(surface.path for surface in self.surfaces if not surface.exists)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": "missipy.local_vector_indexing_smoke_readiness.v1",
            "repository_root": self.repository_root,
            "ready_for_local_smoke": self.ready_for_local_smoke,
            "missing_paths": list(self.missing_paths),
            "surfaces": [surface.to_mapping() for surface in self.surfaces],
            "next_steps": list(self.next_steps),
            "forbidden_new_wheels": list(self.forbidden_new_wheels),
            "decision": "reuse_existing_surfaces_before_runtime_extension",
            "scheduler_remains_orchestrator": True,
            "openvino_import_boundary": "src/inference/openvino_runtime.py",
            "qdrant_projection_boundary": "src/inference/qdrant_projection_adapter.py",
            "sql_durable_authority": "src/context/sql_context_store.py",
        }

    def to_markdown(self) -> str:
        lines = [
            "# Local vector indexing smoke readiness",
            "",
            f"repository_root: `{self.repository_root}`",
            f"ready_for_local_smoke: `{str(self.ready_for_local_smoke).lower()}`",
            "",
            "## Existing surfaces",
            "",
            "| key | status | path | reason |",
            "| --- | --- | --- | --- |",
        ]
        for surface in self.surfaces:
            status = "present" if surface.exists else "missing"
            lines.append(f"| {surface.key} | {status} | `{surface.path}` | {surface.reason} |")
        lines.extend(["", "## Next steps before the first real test", ""])
        for index, step in enumerate(self.next_steps, start=1):
            lines.append(f"{index}. {step}")
        lines.extend(["", "## Forbidden new wheels", ""])
        for wheel in self.forbidden_new_wheels:
            lines.append(f"- {wheel}")
        return "\n".join(lines) + "\n"


def build_local_vector_indexing_smoke_readiness(repository_root: Path) -> LocalVectorIndexingSmokeReadiness:
    root = repository_root.resolve()
    surfaces = tuple(
        SurfaceReadiness(
            key=key,
            path=path,
            reason=reason,
            exists=(root / path).is_file(),
        )
        for key, path, reason in EXPECTED_SURFACES
    )
    return LocalVectorIndexingSmokeReadiness(
        repository_root=str(root),
        surfaces=surfaces,
        next_steps=NEXT_STEPS,
        forbidden_new_wheels=FORBIDDEN_NEW_WHEELS,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan the local vector-indexing smoke test without creating new runtime wheels.")
    parser.add_argument("repository_root", nargs="?", default=".", help="Repository root to inspect")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)

    report = build_local_vector_indexing_smoke_readiness(Path(args.repository_root))
    if args.format == "json":
        print(json.dumps(report.to_mapping(), indent=2, sort_keys=True))
    else:
        print(report.to_markdown(), end="")
    return 0 if report.ready_for_local_smoke else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
