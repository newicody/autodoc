#!/usr/bin/env python3
"""Local artifact to scheduler vector indexing runner using existing surfaces.

0145 turns the validated Scheduler/RouteProxy/vector smoke into a small local
artifact runner.  It does not create a new orchestrator, daemon, Scheduler loop,
OpenVINO adapter, or Qdrant adapter.  It writes an operator artifact input file,
executes the existing scheduler vector indexing smoke tool, and writes a local
artifact result envelope that points to the RouteProxy result frame.

Literal reuse surface: tools/run_local_vector_indexing_live_smoke.py.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Sequence

DEFAULT_MODEL_DIR = "/home/eric/model/openvino/multilingual-e5-small"
DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"
DEFAULT_COLLECTION = "autodoc_smoke_e5_384"
DEFAULT_DIMENSION = 384
DEFAULT_SQL_REF = "sql:artifact/vector-indexing/0145"
DEFAULT_ARTIFACT_TEXT = "passage: Local artifact vector indexing runner sends one artifact through the existing Scheduler route smoke, OpenVINO E5 full-vector handoff, and Qdrant projection."
DEFAULT_ARTIFACT_DIR = ".var/smoke/artifacts/0145"
DEFAULT_ROUTE_ROOT = ".var/smoke/routeproxy-0145/routes"


@dataclass(frozen=True, slots=True)
class LocalArtifactSurface:
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
class LocalArtifactCommand:
    role: str
    argv: tuple[str, ...]

    def shell_preview(self) -> str:
        return " ".join(_shell_quote(value) for value in self.argv)


@dataclass(frozen=True, slots=True)
class LocalArtifactVectorIndexingPlan:
    repository_root: Path
    artifact_dir: Path
    artifact_input: Path
    artifact_report: Path
    artifact_json: Path
    model_dir: Path
    qdrant_url: str
    collection: str
    dimension: int
    sql_ref: str
    route_root: Path
    text: str
    execute: bool
    surfaces: tuple[LocalArtifactSurface, ...]
    commands: tuple[LocalArtifactCommand, ...]

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "artifact_dir": str(self.artifact_dir),
            "artifact_input": str(self.artifact_input),
            "artifact_report": str(self.artifact_report),
            "artifact_json": str(self.artifact_json),
            "model_dir": str(self.model_dir),
            "qdrant_url": self.qdrant_url,
            "collection": self.collection,
            "dimension": self.dimension,
            "sql_ref": self.sql_ref,
            "route_root": str(self.route_root),
            "text": self.text,
            "execute": self.execute,
            "ready_for_local_artifact_vector_indexing": self.ready,
            "surfaces": [surface.to_mapping(root=self.repository_root) for surface in self.surfaces],
            "commands": {command.role: list(command.argv) for command in self.commands},
            "boundary": "existing Scheduler route smoke + existing RouteProxyRuntime + existing OpenVINO/Qdrant tools",
        }

    def to_markdown(self) -> str:
        lines = [
            "# Local artifact vector indexing runner plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"artifact_dir: `{self.artifact_dir}`",
            f"artifact_input: `{self.artifact_input}`",
            f"artifact_report: `{self.artifact_report}`",
            f"artifact_json: `{self.artifact_json}`",
            f"model_dir: `{self.model_dir}`",
            f"qdrant_url: `{self.qdrant_url}`",
            f"collection: `{self.collection}`",
            f"dimension: `{self.dimension}`",
            f"sql_ref: `{self.sql_ref}`",
            f"route_root: `{self.route_root}`",
            f"ready_for_local_artifact_vector_indexing: `{str(self.ready).lower()}`",
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
        lines.extend([
            "",
            "## Artifact text",
            "",
            "```text",
            self.text,
            "```",
            "",
            "## Commands",
            "",
        ])
        for command in self.commands:
            lines.append(f"### {command.role}")
            lines.append("")
            lines.append("```bash")
            lines.append(command.shell_preview())
            lines.append("```")
            lines.append("")
        lines.extend([
            "## Boundary",
            "",
            "- reuses tools/run_scheduler_vector_indexing_smoke.py for Scheduler/RouteProxy/vector execution",
            "- reuses src/runtime/scheduler_route_handler_minimal.py and src/runtime/route_proxy_runtime_minimal.py indirectly",
            "- reuses tools/embed_e5.py --format json --full-vector through the existing smoke chain",
            "- reuses tools/run_qdrant_projection_live_smoke.py --vector-json through the existing smoke chain",
            "- writes local artifact input/report files only under .var/smoke/artifacts/0145 by default",
            "- does not create LocalArtifactOrchestrator",
            "- does not create LocalVectorIndexingOrchestrator",
            "- does not create SchedulerOpenVINORunner",
            "- does not create VectorOpenVINOEmbeddingAdapter",
            "- does not create VectorQdrantProjectionAdapter",
            "- does not modify Scheduler.run()",
            "- SQLContextStore remains durable authority; this runner only carries sql_ref payloads",
        ])
        return "\n".join(lines) + "\n"


@dataclass(frozen=True, slots=True)
class LocalArtifactVectorIndexingResult:
    artifact_input: Path
    artifact_report: Path
    artifact_json: Path
    sql_ref: str
    scheduler_route_frame: str
    local_vector_indexing_smoke: str
    vector_indexing_result_frame: str
    strict_vector_handoff: bool
    machine_vector_handoff: bool
    result_frame_path: str
    point_id: str
    qdrant_rest_id: str
    vector_json: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "artifact_input": str(self.artifact_input),
            "artifact_report": str(self.artifact_report),
            "artifact_json": str(self.artifact_json),
            "sql_ref": self.sql_ref,
            "scheduler_route_frame": self.scheduler_route_frame,
            "local_vector_indexing_smoke": self.local_vector_indexing_smoke,
            "vector_indexing_result_frame": self.vector_indexing_result_frame,
            "strict_vector_handoff": self.strict_vector_handoff,
            "machine_vector_handoff": self.machine_vector_handoff,
            "result_frame_path": self.result_frame_path,
            "point_id": self.point_id,
            "qdrant_rest_id": self.qdrant_rest_id,
            "vector_json": self.vector_json,
            "boundary": "local artifact envelope around existing Scheduler vector indexing smoke",
        }

    def to_markdown(self) -> str:
        return "\n".join([
            "# Local artifact vector indexing result",
            "",
            f"artifact_input: `{self.artifact_input}`",
            f"artifact_report: `{self.artifact_report}`",
            f"artifact_json: `{self.artifact_json}`",
            f"sql_ref: `{self.sql_ref}`",
            f"scheduler_route_frame: `{self.scheduler_route_frame}`",
            f"local_vector_indexing_smoke: `{self.local_vector_indexing_smoke}`",
            f"vector_indexing_result_frame: `{self.vector_indexing_result_frame}`",
            f"strict_vector_handoff: `{str(self.strict_vector_handoff).lower()}`",
            f"machine_vector_handoff: `{str(self.machine_vector_handoff).lower()}`",
            f"result_frame_path: `{self.result_frame_path}`",
            f"point_id: `{self.point_id}`",
            f"qdrant_rest_id: `{self.qdrant_rest_id}`",
            f"vector_json: `{self.vector_json}`",
            "boundary: `local artifact envelope around existing Scheduler vector indexing smoke`",
            "",
        ])


def build_local_artifact_vector_indexing_plan(
    root: Path,
    *,
    artifact_dir: Path,
    model_dir: Path,
    qdrant_url: str,
    collection: str,
    dimension: int,
    sql_ref: str,
    route_root: Path,
    text: str,
    execute: bool,
) -> LocalArtifactVectorIndexingPlan:
    root = root.resolve()
    artifact_dir = _resolve_repo_path(root, artifact_dir)
    route_root = _resolve_repo_path(root, route_root)
    model_dir = model_dir.expanduser()
    text = _ensure_prefix(text, "passage: ")
    artifact_input = artifact_dir / "artifact_input.md"
    artifact_report = artifact_dir / "artifact_vector_indexing_report.md"
    artifact_json = artifact_dir / "artifact_vector_indexing_report.json"
    scheduler_tool = root / "tools" / "run_scheduler_vector_indexing_smoke.py"
    command_args = [
        sys.executable,
        str(scheduler_tool),
        str(root),
        "--model-dir",
        str(model_dir),
        "--qdrant-url",
        qdrant_url,
        "--collection",
        collection,
        "--dimension",
        str(dimension),
        "--sql-ref",
        sql_ref,
        "--route-root",
        str(route_root),
        "--text",
        text,
        "--execute",
    ]
    return LocalArtifactVectorIndexingPlan(
        repository_root=root,
        artifact_dir=artifact_dir,
        artifact_input=artifact_input,
        artifact_report=artifact_report,
        artifact_json=artifact_json,
        model_dir=model_dir,
        qdrant_url=qdrant_url,
        collection=collection,
        dimension=dimension,
        sql_ref=sql_ref,
        route_root=route_root,
        text=text,
        execute=execute,
        surfaces=(
            LocalArtifactSurface(
                key="scheduler_vector_indexing_smoke_tool",
                path=scheduler_tool,
                reason="existing Scheduler/RouteProxy/vector smoke tool from 0143/0144",
            ),
            LocalArtifactSurface(
                key="scheduler_route_handler",
                path=root / "src" / "runtime" / "scheduler_route_handler_minimal.py",
                reason="existing Scheduler route handler surface",
            ),
            LocalArtifactSurface(
                key="route_proxy_runtime",
                path=root / "src" / "runtime" / "route_proxy_runtime_minimal.py",
                reason="existing RouteProxyRuntime frame IO surface",
            ),
            LocalArtifactSurface(
                key="local_vector_indexing_smoke_tool",
                path=root / "tools" / "run_local_vector_indexing_live_smoke.py",
                reason="existing strict OpenVINO/Qdrant vector smoke tool",
            ),
            LocalArtifactSurface(
                key="sql_context_store",
                path=root / "src" / "context" / "sql_context_store.py",
                reason="durable context authority remains SQL",
            ),
        ),
        commands=(
            LocalArtifactCommand(role="scheduler_vector_indexing_smoke", argv=tuple(command_args)),
        ),
    )


def execute_local_artifact_vector_indexing_plan(plan: LocalArtifactVectorIndexingPlan) -> int:
    if not plan.ready:
        return 2
    plan.artifact_dir.mkdir(parents=True, exist_ok=True)
    plan.artifact_input.write_text(plan.text.rstrip() + "\n", encoding="utf-8")
    command = plan.commands[0]
    completed = subprocess.run(
        command.argv,
        cwd=plan.repository_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.stdout:
        print("==> scheduler_vector_indexing_smoke")
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.returncode != 0:
        return completed.returncode
    result = build_local_artifact_vector_indexing_result(plan, completed.stdout or "")
    plan.artifact_json.write_text(json.dumps(result.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.artifact_report.write_text(result.to_markdown(), encoding="utf-8")
    print("==> local_artifact_vector_indexing_result")
    print(result.to_markdown(), end="")
    return 0


def build_local_artifact_vector_indexing_result(plan: LocalArtifactVectorIndexingPlan, output: str) -> LocalArtifactVectorIndexingResult:
    facts = _extract_labelled_facts(output)
    return LocalArtifactVectorIndexingResult(
        artifact_input=plan.artifact_input,
        artifact_report=plan.artifact_report,
        artifact_json=plan.artifact_json,
        sql_ref=plan.sql_ref,
        scheduler_route_frame=str(facts.get("scheduler_route_frame", "unknown")),
        local_vector_indexing_smoke=str(facts.get("local_vector_indexing_smoke", "unknown")),
        vector_indexing_result_frame=str(facts.get("vector_indexing_result_frame", "unknown")),
        strict_vector_handoff=bool(facts.get("strict_vector_handoff", False)),
        machine_vector_handoff=bool(facts.get("machine_vector_handoff", False)),
        result_frame_path=str(facts.get("result_frame_path", "unreported")),
        point_id=str(facts.get("point_id", "qdrant-point:unreported")),
        qdrant_rest_id=str(facts.get("qdrant_rest_id", "unreported")),
        vector_json=str(facts.get("vector_json", str(plan.repository_root / ".var" / "smoke" / "e5_vector_0142.json"))),
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or execute one local artifact through existing Scheduler vector indexing smoke surfaces.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--artifact-dir", type=Path, default=Path(DEFAULT_ARTIFACT_DIR))
    parser.add_argument("--model-dir", type=Path, default=Path(DEFAULT_MODEL_DIR))
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION)
    parser.add_argument("--sql-ref", default=DEFAULT_SQL_REF)
    parser.add_argument("--route-root", type=Path, default=Path(DEFAULT_ROUTE_ROOT))
    parser.add_argument("--text", default=DEFAULT_ARTIFACT_TEXT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    plan = build_local_artifact_vector_indexing_plan(
        args.repository_root,
        artifact_dir=args.artifact_dir,
        model_dir=args.model_dir,
        qdrant_url=args.qdrant_url,
        collection=args.collection,
        dimension=args.dimension,
        sql_ref=args.sql_ref,
        route_root=args.route_root,
        text=args.text,
        execute=args.execute,
    )
    if args.format == "json":
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))
    else:
        print(plan.to_markdown(), end="")
    if not plan.ready:
        return 2
    if args.execute:
        return execute_local_artifact_vector_indexing_plan(plan)
    return 0


def _extract_labelled_facts(output: str) -> dict[str, Any]:
    keys = {
        "scheduler_route_frame",
        "local_vector_indexing_smoke",
        "vector_indexing_result_frame",
        "strict_vector_handoff",
        "machine_vector_handoff",
        "result_frame_path",
        "point_id",
        "qdrant_rest_id",
        "vector_json",
    }
    facts: dict[str, Any] = {}
    for line in output.splitlines():
        match = re.match(r"^([a-zA-Z0-9_]+):\s+`([^`]*)`\s*$", line.strip())
        if not match:
            continue
        key, value = match.groups()
        if key not in keys:
            continue
        if value.lower() == "true":
            facts[key] = True
        elif value.lower() == "false":
            facts[key] = False
        else:
            facts[key] = value
    return facts


def _resolve_repo_path(root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return root / path


def _ensure_prefix(text: str, prefix: str) -> str:
    return text if text.startswith(("query: ", "passage: ")) else prefix + text


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _shell_quote(value: str) -> str:
    if not value:
        return "''"
    if all(ch.isalnum() or ch in "@%_+=:,./-" for ch in value):
        return value
    return "'" + value.replace("'", "'\\''") + "'"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
