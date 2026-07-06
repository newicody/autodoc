#!/usr/bin/env python3
"""Compose the existing P1 artifact/vector/SQL surfaces into one operator smoke.

0158-r1 is an operator composition layer. It calls the existing tools from
0145, 0148, 0149, 0150 and 0151/0152 in sequence and writes a final
closed-loop report. It does not create a Scheduler runner, SQL worker,
orchestrator, OpenVINO adapter, Qdrant adapter or durable database backend.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence


DEFAULT_MODEL_DIR = "/home/eric/model/openvino/multilingual-e5-small"
DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"
DEFAULT_COLLECTION = "autodoc_smoke_e5_384"
DEFAULT_DIMENSION = 384
DEFAULT_SQL_REF = "sql:artifact/vector-indexing/0158"
DEFAULT_HANDOFF_REF = "sql-handoff:sql-persistence/0158"
DEFAULT_ARTIFACT_REF = "artifact:local/0158/smoke"
DEFAULT_VECTOR_INDEXING_JOB_REF = "vector-indexing-job:artifact/0158-smoke"
DEFAULT_TEXT_KIND = "passage"
DEFAULT_TEXT = "passage: P1 closed loop 0158 validates artifact vector indexing before SQL persistence."
DEFAULT_OUTPUT_DIR = ".var/smoke/artifacts/0158"
DEFAULT_ROUTE_ROOT = ".var/smoke/routeproxy-0158/routes"
DEFAULT_DB_PATH = ".var/local/sql_context_store.sqlite3"

# Literal inventory kept for code-rule checks and operator audit readability.
# The command builder below still resolves paths from repository_root.
_REUSED_OPERATOR_TOOL_PATHS = (
    "tools/run_local_artifact_vector_indexing_runner.py",
    "tools/run_sql_persistence_handoff_smoke.py",
    "tools/run_sql_context_store_persistence_smoke.py",
    "tools/run_sql_context_store_write_surface_audit.py",
    "tools/run_sql_context_store_controlled_write_smoke.py",
)

_FORBIDDEN_PARALLEL_SURFACES = (
    "SQLPersistenceWorker",
    "SQLOrchestrator",
    "LocalArtifactOrchestrator",
    "LocalVectorIndexingOrchestrator",
    "SchedulerOpenVINORunner",
    "VectorOpenVINOEmbeddingAdapter",
    "VectorQdrantProjectionAdapter",
)

_SELECTED_WRITE_SURFACE = "DbApiSqlContextStore.upsert_record"


@dataclass(frozen=True, slots=True)
class P1ClosedLoopSurface:
    key: str
    path: Path
    reason: str
    required: bool = True

    def to_mapping(self, *, root: Path) -> dict[str, Any]:
        return {
            "key": self.key,
            "status": "present" if self.path.exists() else "missing",
            "path": _display_path(self.path, root=root),
            "reason": self.reason,
            "required": self.required,
        }


@dataclass(frozen=True, slots=True)
class P1ClosedLoopCommand:
    role: str
    argv: tuple[str, ...]

    def shell_preview(self) -> str:
        return " ".join(_shell_quote(value) for value in self.argv)


@dataclass(frozen=True, slots=True)
class P1ClosedLoopPlan:
    repository_root: Path
    output_dir: Path
    route_root: Path
    artifact_json: Path
    artifact_contract: Path
    result_frame: Path
    handoff_json: Path
    persistence_json: Path
    write_json: Path
    closed_loop_json: Path
    closed_loop_report: Path
    model_dir: Path
    qdrant_url: str
    collection: str
    dimension: int
    sql_ref: str
    handoff_ref: str
    db_path: Path
    text: str
    text_kind: str
    execute: bool
    surfaces: tuple[P1ClosedLoopSurface, ...]
    commands: tuple[P1ClosedLoopCommand, ...]

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces if surface.required)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "output_dir": str(self.output_dir),
            "route_root": str(self.route_root),
            "artifact_json": str(self.artifact_json),
            "artifact_contract": str(self.artifact_contract),
            "result_frame": str(self.result_frame),
            "handoff_json": str(self.handoff_json),
            "persistence_json": str(self.persistence_json),
            "write_json": str(self.write_json),
            "closed_loop_json": str(self.closed_loop_json),
            "closed_loop_report": str(self.closed_loop_report),
            "model_dir": str(self.model_dir),
            "qdrant_url": self.qdrant_url,
            "collection": self.collection,
            "dimension": self.dimension,
            "sql_ref": self.sql_ref,
            "handoff_ref": self.handoff_ref,
            "db_path": str(self.db_path),
            "text": self.text,
            "text_kind": self.text_kind,
            "execute": self.execute,
            "ready_for_p1_closed_loop_operator": self.ready,
            "surfaces": [surface.to_mapping(root=self.repository_root) for surface in self.surfaces],
            "commands": {command.role: list(command.argv) for command in self.commands},
            "boundary": [
                "operator-only composition of existing P1 tools",
                "reuses 0145 local artifact vector indexing runner",
                "reuses 0148 SQL persistence handoff",
                "reuses 0149 SQLContextStore persistence record",
                "reuses 0150 SQL write surface audit",
                "reuses 0151/0152 DbApiSqlContextStore.upsert_record controlled write",
                "does not create SQLPersistenceWorker",
                "does not create SQLOrchestrator",
                "does not create LocalArtifactOrchestrator",
                "does not create LocalVectorIndexingOrchestrator",
                "does not create SchedulerOpenVINORunner",
                "does not create VectorOpenVINOEmbeddingAdapter",
                "does not create VectorQdrantProjectionAdapter",
                "does not modify Scheduler or RouteProxy runtime behavior",
            ],
        }

    def to_markdown(self) -> str:
        lines = [
            "# P1 closed-loop operator composition plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"output_dir: `{self.output_dir}`",
            f"route_root: `{self.route_root}`",
            f"artifact_json: `{self.artifact_json}`",
            f"artifact_contract: `{self.artifact_contract}`",
            f"result_frame: `{self.result_frame}`",
            f"handoff_json: `{self.handoff_json}`",
            f"persistence_json: `{self.persistence_json}`",
            f"write_json: `{self.write_json}`",
            f"closed_loop_json: `{self.closed_loop_json}`",
            f"closed_loop_report: `{self.closed_loop_report}`",
            f"sql_ref: `{self.sql_ref}`",
            f"handoff_ref: `{self.handoff_ref}`",
            f"db_path: `{self.db_path}`",
            f"ready_for_p1_closed_loop_operator: `{str(self.ready).lower()}`",
            f"execute: `{str(self.execute).lower()}`",
            "",
            "## Existing surfaces",
            "",
            "| key | status | required | path | reason |",
            "| --- | --- | --- | --- | --- |",
        ]
        for surface in self.surfaces:
            row = surface.to_mapping(root=self.repository_root)
            lines.append(f"| {row['key']} | {row['status']} | `{str(row['required']).lower()}` | `{row['path']}` | {row['reason']} |")
        lines.extend(["", "## Commands", ""])
        for command in self.commands:
            lines.extend([
                f"### {command.role}",
                "",
                "```bash",
                command.shell_preview(),
                "```",
                "",
            ])
        lines.extend([
            "## Boundary",
            "",
            "- operator-only composition of existing P1 tools",
            "- no Scheduler runner",
            "- no SQL worker",
            "- no orchestrator",
            "- no OpenVINO or Qdrant adapter",
            "- SQL remains durable authority",
            "- Qdrant remains projection/recall metadata",
            "",
        ])
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class P1ClosedLoopResult:
    closed_loop_json: Path
    closed_loop_report: Path
    sql_ref: str
    artifact_ref: str
    handoff_ref: str
    persistence_ref: str
    point_id: str
    qdrant_rest_id: str
    write_status: str
    readback_ok: bool
    selected_store_class: str
    selected_write_method: str
    db_path: str
    status: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "closed_loop_json": str(self.closed_loop_json),
            "closed_loop_report": str(self.closed_loop_report),
            "sql_ref": self.sql_ref,
            "artifact_ref": self.artifact_ref,
            "handoff_ref": self.handoff_ref,
            "persistence_ref": self.persistence_ref,
            "point_id": self.point_id,
            "qdrant_rest_id": self.qdrant_rest_id,
            "write_status": self.write_status,
            "readback_ok": self.readback_ok,
            "selected_store_class": self.selected_store_class,
            "selected_write_method": self.selected_write_method,
            "db_path": self.db_path,
            "status": self.status,
            "boundary": "P1 closed loop composed from existing operator tools; SQL remains durable authority",
        }

    def to_markdown(self) -> str:
        return "\n".join([
            "# P1 closed-loop operator result",
            "",
            f"status: `{self.status}`",
            f"sql_ref: `{self.sql_ref}`",
            f"artifact_ref: `{self.artifact_ref}`",
            f"handoff_ref: `{self.handoff_ref}`",
            f"persistence_ref: `{self.persistence_ref}`",
            f"point_id: `{self.point_id}`",
            f"qdrant_rest_id: `{self.qdrant_rest_id}`",
            f"write_status: `{self.write_status}`",
            f"readback_ok: `{str(self.readback_ok).lower()}`",
            f"selected_store_class: `{self.selected_store_class}`",
            f"selected_write_method: `{self.selected_write_method}`",
            f"db_path: `{self.db_path}`",
            "boundary: `P1 closed loop composed from existing operator tools; SQL remains durable authority`",
            "",
        ])


def build_p1_closed_loop_plan(
    root: Path,
    *,
    output_dir: Path,
    route_root: Path,
    model_dir: Path,
    qdrant_url: str,
    collection: str,
    dimension: int,
    sql_ref: str,
    handoff_ref: str,
    db_path: Path,
    text: str,
    text_kind: str,
    artifact_ref: str,
    vector_indexing_job_ref: str,
    execute: bool,
) -> P1ClosedLoopPlan:
    root = root.resolve()
    output_dir = _resolve_repo_path(root, output_dir)
    route_root = _resolve_repo_path(root, route_root)
    model_dir = model_dir.expanduser()
    db_path = _resolve_repo_path(root, db_path)

    artifact_json = output_dir / "artifact_vector_indexing_report.json"
    artifact_contract = output_dir / "artifact_intake_contract.json"
    result_frame = route_root / "frames" / "vector-route-artifact-local-0158-smoke-job-artifact-0158-smoke-indexing-result.json"
    handoff_json = output_dir / "sql_persistence_handoff.json"
    persistence_json = output_dir / "sql_context_store_persistence_record.json"
    write_json = output_dir / "sql_context_store_controlled_write_result.json"
    closed_loop_json = output_dir / "p1_closed_loop_operator_result.json"
    closed_loop_report = output_dir / "p1_closed_loop_operator_report.md"

    commands = (
        P1ClosedLoopCommand(
            role="0145_local_artifact_vector_indexing",
            argv=(
                sys.executable,
                str(root / "tools" / "run_local_artifact_vector_indexing_runner.py"),
                str(root),
                "--artifact-dir",
                str(output_dir),
                "--artifact-ref",
                artifact_ref,
                "--text-kind",
                text_kind,
                "--vector-indexing-job-ref",
                vector_indexing_job_ref,
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
                _normalize_e5_text(text, text_kind=text_kind),
                "--execute",
                "--format",
                "json",
            ),
        ),
        P1ClosedLoopCommand(
            role="0148_sql_persistence_handoff",
            argv=(
                sys.executable,
                str(root / "tools" / "run_sql_persistence_handoff_smoke.py"),
                str(root),
                "--artifact-json",
                str(artifact_json),
                "--artifact-contract",
                str(artifact_contract),
                "--output-dir",
                str(output_dir),
                "--handoff-ref",
                handoff_ref,
                "--execute",
                "--format",
                "json",
            ),
        ),
        P1ClosedLoopCommand(
            role="0149_sql_context_store_persistence_record",
            argv=(
                sys.executable,
                str(root / "tools" / "run_sql_context_store_persistence_smoke.py"),
                str(root),
                "--handoff-json",
                str(handoff_json),
                "--output-dir",
                str(output_dir),
                "--execute",
                "--format",
                "json",
            ),
        ),
        P1ClosedLoopCommand(
            role="0150_sql_context_store_write_surface_audit",
            argv=(
                sys.executable,
                str(root / "tools" / "run_sql_context_store_write_surface_audit.py"),
                str(root),
                "--persistence-json",
                str(persistence_json),
                "--output-dir",
                str(output_dir),
                "--execute",
                "--format",
                "json",
            ),
        ),
        P1ClosedLoopCommand(
            role="0151_0152_sql_context_store_controlled_write",
            argv=(
                sys.executable,
                str(root / "tools" / "run_sql_context_store_controlled_write_smoke.py"),
                str(root),
                "--persistence-json",
                str(persistence_json),
                "--output-dir",
                str(output_dir),
                "--db-path",
                str(db_path),
                "--execute",
                "--format",
                "json",
            ),
        ),
    )

    return P1ClosedLoopPlan(
        repository_root=root,
        output_dir=output_dir,
        route_root=route_root,
        artifact_json=artifact_json,
        artifact_contract=artifact_contract,
        result_frame=result_frame,
        handoff_json=handoff_json,
        persistence_json=persistence_json,
        write_json=write_json,
        closed_loop_json=closed_loop_json,
        closed_loop_report=closed_loop_report,
        model_dir=model_dir,
        qdrant_url=qdrant_url,
        collection=collection,
        dimension=dimension,
        sql_ref=sql_ref,
        handoff_ref=handoff_ref,
        db_path=db_path,
        text=_normalize_e5_text(text, text_kind=text_kind),
        text_kind=text_kind,
        execute=execute,
        surfaces=(
            P1ClosedLoopSurface("0145_local_artifact_runner", root / "tools" / "run_local_artifact_vector_indexing_runner.py", "existing local artifact vector indexing runner"),
            P1ClosedLoopSurface("0148_sql_handoff", root / "tools" / "run_sql_persistence_handoff_smoke.py", "existing SQL persistence handoff smoke"),
            P1ClosedLoopSurface("0149_sql_persistence_record", root / "tools" / "run_sql_context_store_persistence_smoke.py", "existing SQLContextStore persistence record smoke"),
            P1ClosedLoopSurface("0150_write_surface_audit", root / "tools" / "run_sql_context_store_write_surface_audit.py", "existing SQLContextStore write surface audit"),
            P1ClosedLoopSurface("0151_controlled_sql_write", root / "tools" / "run_sql_context_store_controlled_write_smoke.py", "existing controlled DbApiSqlContextStore write smoke"),
            P1ClosedLoopSurface("sql_context_store", root / "src" / "context" / "sql_context_store.py", "existing durable SQL authority"),
        ),
        commands=commands,
    )


def execute_p1_closed_loop_plan(plan: P1ClosedLoopPlan) -> int:
    if not plan.ready:
        for surface in plan.surfaces:
            if surface.required and not surface.path.exists():
                print(f"missing required surface: {surface.path}", file=sys.stderr)
        return 2

    plan.output_dir.mkdir(parents=True, exist_ok=True)
    for command in plan.commands:
        print(f"==> {command.role}")
        completed = subprocess.run(
            command.argv,
            cwd=plan.repository_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        step_log = plan.output_dir / f"0158_{command.role}.log"
        step_log.write_text(completed.stdout or "", encoding="utf-8")
        if completed.stdout:
            print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
        if completed.returncode != 0:
            return completed.returncode

    result = build_p1_closed_loop_result(plan)
    plan.closed_loop_json.write_text(json.dumps(result.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.closed_loop_report.write_text(result.to_markdown(), encoding="utf-8")
    print("==> p1_closed_loop_operator_result")
    print(result.to_markdown(), end="")
    return 0 if result.status == "ok" else 1


def build_p1_closed_loop_result(plan: P1ClosedLoopPlan) -> P1ClosedLoopResult:
    artifact = _read_json_mapping(plan.artifact_json)
    handoff = _read_json_mapping(plan.handoff_json)
    persistence = _read_json_mapping(plan.persistence_json)
    write = _read_json_mapping(plan.write_json)

    readback_ok = bool(write.get("readback_ok"))
    write_status = str(write.get("write_status", "unknown"))
    status = "ok" if readback_ok and write_status == "persisted" else "failed"

    sql_ref = str(
        write.get(
            "sql_ref",
            persistence.get(
                "sql_ref",
                handoff.get("sql_ref", artifact.get("sql_ref", plan.sql_ref)),
            ),
        )
    )
    artifact_ref = str(
        write.get(
            "artifact_ref",
            persistence.get(
                "artifact_ref",
                handoff.get("artifact_ref", "artifact:unknown"),
            ),
        )
    )
    handoff_ref = str(
        persistence.get(
            "handoff_ref",
            handoff.get("handoff_ref", plan.handoff_ref),
        )
    )
    point_id = str(
        write.get(
            "point_id",
            persistence.get(
                "point_id",
                handoff.get("point_id", artifact.get("point_id", "qdrant-point:unknown")),
            ),
        )
    )
    qdrant_rest_id = str(
        write.get(
            "qdrant_rest_id",
            persistence.get(
                "qdrant_rest_id",
                handoff.get("qdrant_rest_id", artifact.get("qdrant_rest_id", "unknown")),
            ),
        )
    )

    return P1ClosedLoopResult(
        closed_loop_json=plan.closed_loop_json,
        closed_loop_report=plan.closed_loop_report,
        sql_ref=sql_ref,
        artifact_ref=artifact_ref,
        handoff_ref=handoff_ref,
        persistence_ref=str(persistence.get("persistence_ref", "sql-context-persist:unknown")),
        point_id=point_id,
        qdrant_rest_id=qdrant_rest_id,
        write_status=write_status,
        readback_ok=readback_ok,
        selected_store_class=str(write.get("selected_store_class", "unknown")),
        selected_write_method=str(write.get("selected_write_method", "unknown")),
        db_path=str(write.get("db_path", plan.db_path)),
        status=status,
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose existing P1 artifact/vector/SQL smoke tools into one closed-loop operator command.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--route-root", type=Path, default=Path(DEFAULT_ROUTE_ROOT))
    parser.add_argument("--model-dir", type=Path, default=Path(DEFAULT_MODEL_DIR))
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--dimension", type=int, default=DEFAULT_DIMENSION)
    parser.add_argument("--sql-ref", default=DEFAULT_SQL_REF)
    parser.add_argument("--handoff-ref", default=DEFAULT_HANDOFF_REF)
    parser.add_argument("--db-path", type=Path, default=Path(DEFAULT_DB_PATH))
    parser.add_argument("--artifact-ref", default=DEFAULT_ARTIFACT_REF)
    parser.add_argument("--vector-indexing-job-ref", default=DEFAULT_VECTOR_INDEXING_JOB_REF)
    parser.add_argument("--text-kind", choices=("query", "passage"), default=DEFAULT_TEXT_KIND)
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = build_p1_closed_loop_plan(
        args.repository_root,
        output_dir=args.output_dir,
        route_root=args.route_root,
        model_dir=args.model_dir,
        qdrant_url=args.qdrant_url,
        collection=args.collection,
        dimension=args.dimension,
        sql_ref=args.sql_ref,
        handoff_ref=args.handoff_ref,
        db_path=args.db_path,
        text=args.text,
        text_kind=args.text_kind,
        artifact_ref=args.artifact_ref,
        vector_indexing_job_ref=args.vector_indexing_job_ref,
        execute=args.execute,
    )

    if args.format == "json":
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))
    else:
        print(plan.to_markdown(), end="")

    if not args.execute:
        return 0 if plan.ready else 2

    return execute_p1_closed_loop_plan(plan)


def _read_json_mapping(path: Path) -> Mapping[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"expected JSON object in {path}")
    return loaded


def _resolve_repo_path(root: Path, path: Path) -> Path:
    path = path.expanduser()
    if path.is_absolute():
        return path
    return root / path


def _normalize_e5_text(text: str, *, text_kind: str) -> str:
    if text.startswith(("query: ", "passage: ")):
        return text
    return f"{text_kind}: {text}"


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
