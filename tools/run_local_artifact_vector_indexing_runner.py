#!/usr/bin/env python3
"""Local artifact to scheduler vector indexing runner using existing surfaces.

0145 turned the validated Scheduler/RouteProxy/vector smoke into a small local
artifact runner.  0146 adds a pure artifact intake contract in
src/context/artifact_intake_contract.py. 0147 derives dynamic route refs from that
contract instead of forwarding static 0143/0144 smoke refs.  The runner remains an operator
surface: it does not create a new orchestrator, daemon, Scheduler loop,
OpenVINO adapter, or Qdrant adapter.

Literal reuse surface: tools/run_local_vector_indexing_live_smoke.py.
Literal contract surface: src/context/artifact_intake_contract.py.
Literal route ref surface: src/context/artifact_route_refs.py.
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
DEFAULT_SQL_REF = "sql:artifact/vector-indexing/0147"
DEFAULT_ARTIFACT_REF = "artifact:local/0147/smoke"
DEFAULT_ARTIFACT_KIND = "local_markdown"
DEFAULT_TEXT_KIND = "passage"
DEFAULT_VECTOR_INDEXING_JOB_REF = "vector-indexing-job:artifact/0147-smoke"
DEFAULT_ARTIFACT_TEXT = "passage: Local artifact dynamic route refs send one artifact through the existing Scheduler route smoke, OpenVINO E5 full-vector handoff, and Qdrant projection."
DEFAULT_ARTIFACT_DIR = ".var/smoke/artifacts/0147"
DEFAULT_ROUTE_ROOT = ".var/smoke/routeproxy-0147/routes"


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
    artifact_contract_path: Path
    artifact_report: Path
    artifact_json: Path
    model_dir: Path
    qdrant_url: str
    collection: str
    dimension: int
    sql_ref: str
    route_root: Path
    text: str
    artifact_contract: Any
    artifact_route_refs: Any
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
            "artifact_contract_path": str(self.artifact_contract_path),
            "artifact_contract": self.artifact_contract.to_mapping(),
            "artifact_route_refs": self.artifact_route_refs.to_mapping(),
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
            f"artifact_contract_path: `{self.artifact_contract_path}`",
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
            "## Artifact intake contract",
            "",
            f"artifact_ref: `{self.artifact_contract.artifact_ref}`",
            f"artifact_kind: `{self.artifact_contract.artifact_kind}`",
            f"artifact_path: `{self.artifact_contract.artifact_path}`",
            f"text_kind: `{self.artifact_contract.text_kind}`",
            f"vector_indexing_job_ref: `{self.artifact_contract.vector_indexing_job_ref}`",
            "",
            "## Dynamic route refs",
            "",
            f"command_ref: `{self.artifact_route_refs.command_ref}`",
            f"request_route_ref: `{self.artifact_route_refs.request_route_ref}`",
            f"result_command_ref: `{self.artifact_route_refs.result_command_ref}`",
            f"result_route_ref: `{self.artifact_route_refs.result_route_ref}`",
            f"route_namespace: `{self.artifact_route_refs.route_namespace}`",
            f"result_route_namespace: `{self.artifact_route_refs.result_route_namespace}`",
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
            self.artifact_contract.normalized_text(),
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
            "- writes local artifact input/contract/report files only under .var/smoke/artifacts/0147 by default",
            "- reuses src/context/artifact_intake_contract.py as a pure typed intake contract",
            "- reuses src/context/artifact_route_refs.py to derive dynamic command and route refs",
            "- does not forward static 0143/0144 smoke refs when artifact route refs are available",
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
    artifact_contract_path: Path
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
            "artifact_contract_path": str(self.artifact_contract_path),
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
            f"artifact_contract_path: `{self.artifact_contract_path}`",
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
    artifact_ref: str = DEFAULT_ARTIFACT_REF,
    artifact_kind: str = DEFAULT_ARTIFACT_KIND,
    text_kind: str = DEFAULT_TEXT_KIND,
    vector_indexing_job_ref: str = DEFAULT_VECTOR_INDEXING_JOB_REF,
) -> LocalArtifactVectorIndexingPlan:
    root = root.resolve()
    artifact_dir = _resolve_repo_path(root, artifact_dir)
    route_root = _resolve_repo_path(root, route_root)
    model_dir = model_dir.expanduser()
    artifact_input = artifact_dir / "artifact_input.md"
    artifact_contract_path = artifact_dir / "artifact_intake_contract.json"
    artifact_report = artifact_dir / "artifact_vector_indexing_report.md"
    artifact_json = artifact_dir / "artifact_vector_indexing_report.json"
    artifact_contract = _build_artifact_intake_contract(
        root,
        artifact_ref=artifact_ref,
        artifact_kind=artifact_kind,
        artifact_path=artifact_input,
        text_kind=text_kind,
        sql_ref=sql_ref,
        collection=collection,
        dimension=dimension,
        route_root=route_root,
        vector_indexing_job_ref=vector_indexing_job_ref,
        text=text,
    )
    text = artifact_contract.normalized_text()
    artifact_route_refs = _build_artifact_route_refs(
        root,
        artifact_ref=artifact_contract.artifact_ref,
        vector_indexing_job_ref=artifact_contract.vector_indexing_job_ref,
    )
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
        "--command-ref",
        artifact_route_refs.command_ref,
        "--request-route-ref",
        artifact_route_refs.request_route_ref,
        "--result-command-ref",
        artifact_route_refs.result_command_ref,
        "--result-route-ref",
        artifact_route_refs.result_route_ref,
        "--result-owner-ref",
        artifact_route_refs.result_owner_ref,
        "--vector-indexing-job-ref",
        artifact_route_refs.vector_indexing_job_ref,
        "--route-namespace",
        artifact_route_refs.route_namespace,
        "--result-route-namespace",
        artifact_route_refs.result_route_namespace,
        "--text",
        text,
        "--execute",
    ]
    return LocalArtifactVectorIndexingPlan(
        repository_root=root,
        artifact_dir=artifact_dir,
        artifact_input=artifact_input,
        artifact_contract_path=artifact_contract_path,
        artifact_report=artifact_report,
        artifact_json=artifact_json,
        model_dir=model_dir,
        qdrant_url=qdrant_url,
        collection=collection,
        dimension=dimension,
        sql_ref=sql_ref,
        route_root=route_root,
        text=text,
        artifact_contract=artifact_contract,
        artifact_route_refs=artifact_route_refs,
        execute=execute,
        surfaces=(
            LocalArtifactSurface(
                key="scheduler_vector_indexing_smoke_tool",
                path=scheduler_tool,
                reason="existing Scheduler/RouteProxy/vector smoke tool from 0143/0144",
            ),
            LocalArtifactSurface(
                key="artifact_intake_contract",
                path=_artifact_intake_contract_surface_path(root),
                reason="pure typed artifact intake contract from 0146",
            ),
            LocalArtifactSurface(
                key="artifact_route_refs",
                path=_artifact_route_refs_surface_path(root),
                reason="pure dynamic route refs from 0147",
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
    plan.artifact_input.write_text(plan.artifact_contract.normalized_text().rstrip() + "\n", encoding="utf-8")
    plan.artifact_contract_path.write_text(json.dumps(plan.artifact_contract.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
        artifact_contract_path=plan.artifact_contract_path,
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
    parser.add_argument("--artifact-ref", default=DEFAULT_ARTIFACT_REF)
    parser.add_argument("--artifact-kind", default=DEFAULT_ARTIFACT_KIND)
    parser.add_argument("--text-kind", choices=("query", "passage"), default=DEFAULT_TEXT_KIND)
    parser.add_argument("--vector-indexing-job-ref", default=DEFAULT_VECTOR_INDEXING_JOB_REF)
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
        artifact_ref=args.artifact_ref,
        artifact_kind=args.artifact_kind,
        text_kind=args.text_kind,
        vector_indexing_job_ref=args.vector_indexing_job_ref,
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


def _artifact_intake_contract_surface_path(root: Path) -> Path:
    candidate = root / "src" / "context" / "artifact_intake_contract.py"
    if candidate.exists():
        return candidate
    return Path(__file__).resolve().parents[1] / "src" / "context" / "artifact_intake_contract.py"


def _artifact_route_refs_surface_path(root: Path) -> Path:
    candidate = root / "src" / "context" / "artifact_route_refs.py"
    if candidate.exists():
        return candidate
    return Path(__file__).resolve().parents[1] / "src" / "context" / "artifact_route_refs.py"


def _build_artifact_route_refs(root: Path, **kwargs: Any) -> Any:
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from context.artifact_route_refs import build_artifact_route_refs

    return build_artifact_route_refs(**kwargs)


def _build_artifact_intake_contract(root: Path, **kwargs: Any) -> Any:
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from context.artifact_intake_contract import build_artifact_intake_contract

    return build_artifact_intake_contract(**kwargs)


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
