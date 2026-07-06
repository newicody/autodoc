#!/usr/bin/env python3
"""Scheduler route to local vector indexing smoke through existing surfaces.

0143 does not create a Scheduler runner, OpenVINO adapter, Qdrant adapter, or
RouteProxy worker.  It proves that a Scheduler-shaped handler command can write
a vector indexing request frame through the existing RouteProxy runtime and then
handoff to the already validated strict local vector indexing smoke tool.

The live backend path remains outside Scheduler and RouteProxy:

Scheduler-shaped command -> existing scheduler_route_handler_minimal -> existing
RouteProxyRuntime frame -> tools/run_local_vector_indexing_live_smoke.py ->
existing OpenVINO/E5 + existing Qdrant smoke tools.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Sequence

DEFAULT_MODEL_DIR = "/home/eric/model/openvino/multilingual-e5-small"
DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"
DEFAULT_COLLECTION = "autodoc_smoke_e5_384"
DEFAULT_DIMENSION = 384
DEFAULT_SQL_REF = "sql:smoke/vector-indexing/0143"
DEFAULT_CONTEXT_REF = "sql:smoke/vector-indexing/0143"
DEFAULT_TEXT = "passage: Scheduler route handler writes a vector indexing request frame; existing local vector smoke executes OpenVINO E5 then Qdrant projection."
DEFAULT_ROUTE_REF = "vector-route:smoke/0143/embedding-request"
DEFAULT_RESULT_ROUTE_REF = "vector-route:smoke/0144/indexing-result"
DEFAULT_ROUTE_ROOT = ".var/smoke/routeproxy-0143/routes"


@dataclass(frozen=True, slots=True)
class SchedulerVectorSmokeSurface:
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
class SchedulerVectorSmokeCommand:
    role: str
    argv: tuple[str, ...]

    def shell_preview(self) -> str:
        return " ".join(_shell_quote(part) for part in self.argv)


@dataclass(frozen=True, slots=True)
class SchedulerRouteFramePreview:
    route_ref: str
    owner_ref: str
    context_ref: str
    context_generation: int
    priority: int
    frame_kind: str
    payload: dict[str, Any]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "route_ref": self.route_ref,
            "owner_ref": self.owner_ref,
            "context_ref": self.context_ref,
            "context_generation": self.context_generation,
            "priority": self.priority,
            "frame_kind": self.frame_kind,
            "payload": self.payload,
        }


@dataclass(frozen=True, slots=True)
class SchedulerRouteFrameWriteSummary:
    command_ref: str
    route_root: Path
    written_route_refs: tuple[str, ...]
    readback_count: int
    frame_paths: tuple[Path, ...]
    payload_frame_kind: str
    payload_sql_ref: str
    payload_operator_tool: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "command_ref": self.command_ref,
            "route_root": str(self.route_root),
            "written_route_refs": list(self.written_route_refs),
            "readback_count": self.readback_count,
            "frame_paths": [str(path) for path in self.frame_paths],
            "payload_frame_kind": self.payload_frame_kind,
            "payload_sql_ref": self.payload_sql_ref,
            "payload_operator_tool": self.payload_operator_tool,
            "scheduler_route_handler": "existing",
            "route_proxy_runtime": "existing",
            "scheduler_run_modified": False,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Scheduler route frame write result",
            "",
            f"command_ref: `{self.command_ref}`",
            f"route_root: `{self.route_root}`",
            f"written_route_refs: `{', '.join(self.written_route_refs)}`",
            f"readback_count: `{self.readback_count}`",
            f"payload_frame_kind: `{self.payload_frame_kind}`",
            f"payload_sql_ref: `{self.payload_sql_ref}`",
            f"payload_operator_tool: `{self.payload_operator_tool}`",
            "",
            "## Frame paths",
            "",
        ]
        for path in self.frame_paths:
            lines.append(f"- `{path}`")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True, slots=True)
class SchedulerVectorIndexingResultFrameSummary:
    command_ref: str
    route_root: Path
    result_route_ref: str
    result_frame_path: Path
    status: str
    sql_ref: str
    point_id: str
    qdrant_rest_id: str
    machine_vector_handoff: bool
    strict_vector_handoff: bool
    vector_json: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "command_ref": self.command_ref,
            "route_root": str(self.route_root),
            "result_route_ref": self.result_route_ref,
            "result_frame_path": str(self.result_frame_path),
            "status": self.status,
            "sql_ref": self.sql_ref,
            "point_id": self.point_id,
            "qdrant_rest_id": self.qdrant_rest_id,
            "machine_vector_handoff": self.machine_vector_handoff,
            "strict_vector_handoff": self.strict_vector_handoff,
            "vector_json": self.vector_json,
            "scheduler_route_handler": "existing",
            "route_proxy_runtime": "existing",
            "scheduler_run_modified": False,
        }

    def to_markdown(self) -> str:
        return "\n".join([
            "# Scheduler vector indexing result frame",
            "",
            f"command_ref: `{self.command_ref}`",
            f"route_root: `{self.route_root}`",
            f"result_route_ref: `{self.result_route_ref}`",
            f"result_frame_path: `{self.result_frame_path}`",
            f"status: `{self.status}`",
            f"sql_ref: `{self.sql_ref}`",
            f"point_id: `{self.point_id}`",
            f"qdrant_rest_id: `{self.qdrant_rest_id}`",
            f"machine_vector_handoff: `{str(self.machine_vector_handoff).lower()}`",
            f"strict_vector_handoff: `{str(self.strict_vector_handoff).lower()}`",
            f"vector_json: `{self.vector_json}`",
            "boundary: `existing Scheduler route handler + existing RouteProxyRuntime result frame`",
            "",
        ])


@dataclass(frozen=True, slots=True)
class SchedulerVectorIndexingSmokePlan:
    repository_root: Path
    model_dir: Path
    qdrant_url: str
    collection: str
    dimension: int
    sql_ref: str
    route_root: Path
    execute: bool
    strict_vector_handoff: bool
    text: str
    surfaces: tuple[SchedulerVectorSmokeSurface, ...]
    route_frame_preview: SchedulerRouteFramePreview
    commands: tuple[SchedulerVectorSmokeCommand, ...]

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces)

    def missing_surfaces(self) -> tuple[SchedulerVectorSmokeSurface, ...]:
        return tuple(surface for surface in self.surfaces if not surface.path.exists())

    def to_markdown(self) -> str:
        lines = [
            "# Scheduler vector indexing smoke plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"model_dir: `{self.model_dir}`",
            f"qdrant_url: `{self.qdrant_url}`",
            f"collection: `{self.collection}`",
            f"dimension: `{self.dimension}`",
            f"sql_ref: `{self.sql_ref}`",
            f"route_root: `{self.route_root}`",
            f"ready_for_scheduler_vector_indexing_smoke: `{str(self.ready).lower()}`",
            f"strict_vector_handoff: `{str(self.strict_vector_handoff).lower()}`",
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
            "## Scheduler route frame preview",
            "",
            "```json",
            json.dumps(self.route_frame_preview.to_mapping(), indent=2, sort_keys=True),
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
            "- reuses src/runtime/scheduler_route_handler_minimal.py as existing handler surface",
            "- reuses src/runtime/route_proxy_runtime_minimal.py for RouteProxy frame IO",
            "- reuses tools/run_local_vector_indexing_live_smoke.py for strict vector execution",
            "- reuses tools/embed_e5.py --format json --full-vector through the local vector smoke tool",
            "- reuses tools/run_qdrant_projection_live_smoke.py --vector-json through the local vector smoke tool",
            "- does not create SchedulerOpenVINORunner",
            "- does not create LocalVectorIndexingOrchestrator",
            "- does not create VectorOpenVINOEmbeddingAdapter",
            "- does not create VectorQdrantProjectionAdapter",
            "- does not modify the Scheduler run loop",
            "- Scheduler writes a request frame; OpenVINO and Qdrant stay behind operator tools and existing adapters",
            "- 0144 writes a vector_indexing_result frame back through the existing RouteProxyRuntime",
        ])
        return "\n".join(lines) + "\n"


def build_scheduler_vector_indexing_smoke_plan(
    root: Path,
    *,
    model_dir: Path,
    qdrant_url: str,
    collection: str,
    dimension: int,
    sql_ref: str,
    route_root: Path,
    text: str,
    execute: bool,
    strict_vector_handoff: bool,
    context_generation: int = 1,
    priority: int = 900,
) -> SchedulerVectorIndexingSmokePlan:
    root = root.resolve()
    model_dir = model_dir.expanduser()
    route_root = _resolve_repo_path(root, route_root)
    text = _ensure_prefix(text, "passage: ")
    local_tool = root / "tools" / "run_local_vector_indexing_live_smoke.py"
    vector_json = root / ".var" / "smoke" / "e5_vector_0142.json"
    payload = {
        "frame_kind": "vector_embedding_request",
        "vector_indexing_job_ref": "vector-indexing-job:0143-smoke",
        "text": text,
        "text_kind": "passage",
        "model_dir": str(model_dir),
        "qdrant_url": qdrant_url,
        "collection": collection,
        "dimension": dimension,
        "sql_ref": sql_ref,
        "strict_vector_handoff": strict_vector_handoff,
        "vector_json": str(vector_json),
        "operator_tool": "tools/run_local_vector_indexing_live_smoke.py",
        "scheduler_run_modified": False,
    }
    route_frame_preview = SchedulerRouteFramePreview(
        route_ref=DEFAULT_ROUTE_REF,
        owner_ref="scheduler-command:vector-indexing-smoke-0143",
        context_ref=sql_ref,
        context_generation=context_generation,
        priority=priority,
        frame_kind="vector_embedding_request",
        payload=payload,
    )
    command_args = [
        sys.executable,
        str(local_tool),
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
    ]
    if strict_vector_handoff:
        command_args.append("--strict-vector-handoff")
    command_args.append("--execute")
    return SchedulerVectorIndexingSmokePlan(
        repository_root=root,
        model_dir=model_dir,
        qdrant_url=qdrant_url,
        collection=collection,
        dimension=dimension,
        sql_ref=sql_ref,
        route_root=route_root,
        execute=execute,
        strict_vector_handoff=strict_vector_handoff,
        text=text,
        surfaces=(
            SchedulerVectorSmokeSurface(
                key="scheduler_route_handler",
                path=root / "src" / "runtime" / "scheduler_route_handler_minimal.py",
                reason="existing Scheduler route handler extended in 0131/0133",
            ),
            SchedulerVectorSmokeSurface(
                key="route_proxy_runtime",
                path=root / "src" / "runtime" / "route_proxy_runtime_minimal.py",
                reason="existing RouteProxyRuntime frame IO from 0130",
            ),
            SchedulerVectorSmokeSurface(
                key="local_vector_indexing_smoke_tool",
                path=local_tool,
                reason="existing strict local vector smoke tool from 0141/0142",
            ),
            SchedulerVectorSmokeSurface(
                key="vector_indexing_job_plan",
                path=root / "src" / "context" / "vector_indexing_job_plan.py",
                reason="existing vector indexing job contract from 0128",
            ),
            SchedulerVectorSmokeSurface(
                key="openvino_embedding_membrane",
                path=root / "src" / "inference" / "openvino_embedding_adapter.py",
                reason="existing OpenVINO/E5 embedding membrane",
            ),
            SchedulerVectorSmokeSurface(
                key="qdrant_projection_adapter",
                path=root / "src" / "inference" / "qdrant_projection_adapter.py",
                reason="existing Qdrant projection membrane",
            ),
        ),
        route_frame_preview=route_frame_preview,
        commands=(
            SchedulerVectorSmokeCommand(
                role="local_vector_indexing_live_smoke",
                argv=tuple(command_args),
            ),
        ),
    )


def write_scheduler_vector_indexing_request_frame(plan: SchedulerVectorIndexingSmokePlan) -> SchedulerRouteFrameWriteSummary:
    """Write the vector indexing request frame through the existing handler/runtime."""

    _ensure_runtime_import_path(plan.repository_root)
    handler_module = importlib.import_module("runtime.scheduler_route_handler_minimal")
    route_runtime_module = importlib.import_module("runtime.route_proxy_runtime_minimal")
    policy = route_runtime_module.RouteProxyRuntimePolicy(
        route_root=plan.route_root,
        require_dev_shm=False,
        allow_test_root=True,
        namespace="autodoc-smoke-0143",
    )
    if plan.route_root.exists():
        shutil.rmtree(plan.route_root)
    command = handler_module.build_single_frame_route_command(
        command_ref="scheduler-command:vector-indexing-smoke-0143",
        route_ref=plan.route_frame_preview.route_ref,
        owner_ref=plan.route_frame_preview.owner_ref,
        context_ref=plan.route_frame_preview.context_ref,
        context_generation=plan.route_frame_preview.context_generation,
        priority=plan.route_frame_preview.priority,
        frame_kind=plan.route_frame_preview.frame_kind,
        payload=plan.route_frame_preview.payload,
        runtime_policy=policy,
    )
    readback = handler_module.handle_scheduler_route_command_with_readback(command)
    if not readback.readback_frames:
        raise RuntimeError("existing scheduler route handler did not write a readable frame")
    frame = readback.readback_frames[0]
    payload = frame.payload
    return SchedulerRouteFrameWriteSummary(
        command_ref=command.command_ref,
        route_root=plan.route_root,
        written_route_refs=tuple(readback.handler_result.written_route_refs),
        readback_count=len(readback.readback_frames),
        frame_paths=tuple(readback.handler_result.frame_paths),
        payload_frame_kind=str(payload.get("frame_kind")),
        payload_sql_ref=str(payload.get("sql_ref")),
        payload_operator_tool=str(payload.get("operator_tool")),
    )


def extract_vector_indexing_smoke_result(output: str) -> dict[str, Any]:
    """Extract machine-readable smoke facts from markdown output.

    This parser only reads labelled result lines emitted by existing smoke tools.
    It does not parse human-only values_preview vectors and does not infer a vector.
    """

    keys = {
        "point_id",
        "qdrant_rest_id",
        "upsert_acknowledged",
        "machine_vector_handoff",
        "machine_vector_available",
        "strict_vector_handoff",
        "vector_json",
        "openvino_e5_smoke",
        "qdrant_projection_smoke",
    }
    parsed: dict[str, Any] = {}
    for line in output.splitlines():
        match = re.match(r"^([a-zA-Z0-9_]+):\s+`([^`]*)`\s*$", line.strip())
        if not match:
            continue
        key, value = match.groups()
        if key not in keys:
            continue
        if value.lower() == "true":
            parsed[key] = True
        elif value.lower() == "false":
            parsed[key] = False
        else:
            parsed[key] = value
    return parsed


def write_scheduler_vector_indexing_result_frame(
    plan: SchedulerVectorIndexingSmokePlan,
    *,
    request_summary: SchedulerRouteFrameWriteSummary,
    smoke_output: str,
) -> SchedulerVectorIndexingResultFrameSummary:
    """Write a vector_indexing_result frame through the existing handler/runtime."""

    facts = extract_vector_indexing_smoke_result(smoke_output)
    point_id = str(facts.get("point_id", "qdrant-point:unreported"))
    qdrant_rest_id = str(facts.get("qdrant_rest_id", "unreported"))
    vector_json = str(facts.get("vector_json", str(plan.repository_root / ".var" / "smoke" / "e5_vector_0142.json")))
    machine_vector_handoff = bool(facts.get("machine_vector_handoff", facts.get("machine_vector_available", False)))
    strict_vector_handoff = bool(facts.get("strict_vector_handoff", plan.strict_vector_handoff))
    status = "ok" if str(facts.get("qdrant_projection_smoke", "ok")) == "ok" else "unknown"

    _ensure_runtime_import_path(plan.repository_root)
    handler_module = importlib.import_module("runtime.scheduler_route_handler_minimal")
    route_runtime_module = importlib.import_module("runtime.route_proxy_runtime_minimal")
    policy = route_runtime_module.RouteProxyRuntimePolicy(
        route_root=plan.route_root,
        require_dev_shm=False,
        allow_test_root=True,
        namespace="autodoc-smoke-0144",
    )
    payload = {
        "frame_kind": "vector_indexing_result",
        "request_route_ref": plan.route_frame_preview.route_ref,
        "request_frame_paths": [str(path) for path in request_summary.frame_paths],
        "sql_ref": plan.sql_ref,
        "status": status,
        "point_id": point_id,
        "qdrant_rest_id": qdrant_rest_id,
        "vector_json": vector_json,
        "machine_vector_handoff": machine_vector_handoff,
        "strict_vector_handoff": strict_vector_handoff,
        "operator_tool": "tools/run_local_vector_indexing_live_smoke.py",
        "scheduler_run_modified": False,
    }
    command = handler_module.build_single_frame_route_command(
        command_ref="scheduler-command:vector-indexing-smoke-0144-result",
        route_ref=DEFAULT_RESULT_ROUTE_REF,
        owner_ref="worker:local-vector-indexing-smoke",
        context_ref=plan.sql_ref,
        context_generation=plan.route_frame_preview.context_generation,
        priority=plan.route_frame_preview.priority,
        frame_kind="vector_indexing_result",
        payload=payload,
        runtime_policy=policy,
    )
    readback = handler_module.handle_scheduler_route_command_with_readback(command)
    if not readback.readback_frames:
        raise RuntimeError("existing scheduler route handler did not write a readable result frame")
    result_frame = readback.readback_frames[0]
    result_payload = result_frame.payload
    return SchedulerVectorIndexingResultFrameSummary(
        command_ref=command.command_ref,
        route_root=plan.route_root,
        result_route_ref=DEFAULT_RESULT_ROUTE_REF,
        result_frame_path=readback.handler_result.frame_paths[0],
        status=str(result_payload.get("status")),
        sql_ref=str(result_payload.get("sql_ref")),
        point_id=str(result_payload.get("point_id")),
        qdrant_rest_id=str(result_payload.get("qdrant_rest_id")),
        machine_vector_handoff=bool(result_payload.get("machine_vector_handoff")),
        strict_vector_handoff=bool(result_payload.get("strict_vector_handoff")),
        vector_json=str(result_payload.get("vector_json")),
    )


def execute_scheduler_vector_indexing_smoke(plan: SchedulerVectorIndexingSmokePlan) -> int:
    """Write the Scheduler route frame, then call the existing local vector smoke."""

    if not plan.ready:
        for surface in plan.missing_surfaces():
            print(f"missing surface: {surface.path}", file=sys.stderr)
        return 2
    print("==> scheduler_route_frame")
    write_summary = write_scheduler_vector_indexing_request_frame(plan)
    print(write_summary.to_markdown(), end="")
    print("==> local_vector_indexing_live_smoke")
    result = subprocess.run(
        plan.commands[0].argv,
        cwd=plan.repository_root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.returncode != 0:
        return result.returncode
    print("==> vector_indexing_result_frame")
    result_summary = write_scheduler_vector_indexing_result_frame(
        plan,
        request_summary=write_summary,
        smoke_output=result.stdout or "",
    )
    print(result_summary.to_markdown(), end="")
    print("# Scheduler vector indexing smoke result")
    print("")
    print("scheduler_route_frame: `ok`")
    print("local_vector_indexing_smoke: `ok`")
    print("vector_indexing_result_frame: `ok`")
    print("strict_vector_handoff: `" + str(result_summary.strict_vector_handoff).lower() + "`")
    print("machine_vector_handoff: `" + str(result_summary.machine_vector_handoff).lower() + "`")
    print("result_frame_path: `" + str(result_summary.result_frame_path) + "`")
    print("boundary: `existing Scheduler route handler + existing RouteProxyRuntime + existing local vector smoke tool + result frame`")
    return 0


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or execute Scheduler route to vector indexing smoke through existing surfaces.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--model-dir", type=Path, default=Path(DEFAULT_MODEL_DIR))
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION)
    parser.add_argument("--sql-ref", default=DEFAULT_SQL_REF)
    parser.add_argument("--route-root", type=Path, default=Path(DEFAULT_ROUTE_ROOT))
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--strict-vector-handoff", action="store_true", default=True)
    parser.add_argument("--no-strict-vector-handoff", action="store_false", dest="strict_vector_handoff")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    plan = build_scheduler_vector_indexing_smoke_plan(
        args.repository_root,
        model_dir=args.model_dir,
        qdrant_url=args.qdrant_url,
        collection=args.collection,
        dimension=args.dimension,
        sql_ref=args.sql_ref,
        route_root=args.route_root,
        text=args.text,
        execute=args.execute,
        strict_vector_handoff=args.strict_vector_handoff,
    )
    if args.format == "json":
        print(json.dumps(_plan_to_mapping(plan), indent=2, sort_keys=True))
    else:
        print(plan.to_markdown(), end="")
    if not plan.ready:
        return 2
    if args.execute:
        return execute_scheduler_vector_indexing_smoke(plan)
    return 0


def _plan_to_mapping(plan: SchedulerVectorIndexingSmokePlan) -> dict[str, Any]:
    return {
        "repository_root": str(plan.repository_root),
        "model_dir": str(plan.model_dir),
        "qdrant_url": plan.qdrant_url,
        "collection": plan.collection,
        "dimension": plan.dimension,
        "sql_ref": plan.sql_ref,
        "route_root": str(plan.route_root),
        "ready_for_scheduler_vector_indexing_smoke": plan.ready,
        "strict_vector_handoff": plan.strict_vector_handoff,
        "execute": plan.execute,
        "surfaces": [surface.to_mapping(root=plan.repository_root) for surface in plan.surfaces],
        "route_frame_preview": plan.route_frame_preview.to_mapping(),
        "commands": {command.role: list(command.argv) for command in plan.commands},
    }


def _ensure_runtime_import_path(root: Path) -> None:
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


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
