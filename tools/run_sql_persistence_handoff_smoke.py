#!/usr/bin/env python3
"""Build a SQL persistence handoff envelope from artifact vector results.

0148 is handoff-only. It does not write a database row, does not create a SQL
worker, and does not turn Qdrant into durable truth. The output is a structured
JSON/Markdown envelope ready for the existing SQLContextStore path in a later
patch.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

DEFAULT_ARTIFACT_JSON = ".var/smoke/artifacts/0147/artifact_vector_indexing_report.json"
DEFAULT_OUTPUT_DIR = ".var/smoke/artifacts/0148"


@dataclass(frozen=True, slots=True)
class SqlHandoffSurface:
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
class SqlPersistenceHandoffPlan:
    repository_root: Path
    artifact_json: Path
    artifact_contract_path: Path | None
    result_frame_path: Path | None
    output_dir: Path
    handoff_json: Path
    handoff_report: Path
    handoff_ref: str
    execute: bool
    surfaces: tuple[SqlHandoffSurface, ...]

    @property
    def ready(self) -> bool:
        return self.artifact_json.exists() and all(
            surface.path.exists() for surface in self.surfaces if surface.required
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "artifact_json": str(self.artifact_json),
            "artifact_contract_path": str(self.artifact_contract_path) if self.artifact_contract_path else "auto-from-artifact-json",
            "result_frame_path": str(self.result_frame_path) if self.result_frame_path else "auto-from-artifact-json",
            "output_dir": str(self.output_dir),
            "handoff_json": str(self.handoff_json),
            "handoff_report": str(self.handoff_report),
            "handoff_ref": self.handoff_ref,
            "ready_for_sql_persistence_handoff": self.ready,
            "execute": self.execute,
            "surfaces": [surface.to_mapping(root=self.repository_root) for surface in self.surfaces],
            "boundary": "handoff-only envelope for existing SQLContextStore path; no SQL write in 0148",
        }

    def to_markdown(self) -> str:
        lines = [
            "# SQL persistence handoff smoke plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"artifact_json: `{self.artifact_json}`",
            f"artifact_contract_path: `{self.artifact_contract_path if self.artifact_contract_path else 'auto-from-artifact-json'}`",
            f"result_frame_path: `{self.result_frame_path if self.result_frame_path else 'auto-from-artifact-json'}`",
            f"output_dir: `{self.output_dir}`",
            f"handoff_json: `{self.handoff_json}`",
            f"handoff_report: `{self.handoff_report}`",
            f"handoff_ref: `{self.handoff_ref}`",
            f"ready_for_sql_persistence_handoff: `{str(self.ready).lower()}`",
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
        lines.extend([
            "",
            "## Boundary",
            "",
            "- handoff-only envelope for existing SQLContextStore path",
            "- reuses src/context/sql_persistence_handoff_contract.py as a pure contract",
            "- consumes artifact_vector_indexing_report.json from the existing artifact runner",
            "- can read artifact_intake_contract.json and the vector_indexing_result frame",
            "- writes sql_persistence_handoff.json and sql_persistence_handoff_report.md only",
            "- does not write to SQL in 0148",
            "- does not create SQLPersistenceWorker",
            "- does not create SQLOrchestrator",
            "- does not import backend clients",
            "- Qdrant remains projection/recall only; SQL remains durable authority",
        ])
        return "\n".join(lines) + "\n"


def build_sql_persistence_handoff_plan(
    root: Path,
    *,
    artifact_json: Path,
    artifact_contract_path: Path | None,
    result_frame_path: Path | None,
    output_dir: Path,
    handoff_ref: str | None,
    execute: bool,
) -> SqlPersistenceHandoffPlan:
    root = root.resolve()
    artifact_json = _resolve_repo_path(root, artifact_json)
    output_dir = _resolve_repo_path(root, output_dir)
    artifact_contract_path = _resolve_repo_path(root, artifact_contract_path) if artifact_contract_path else None
    result_frame_path = _resolve_repo_path(root, result_frame_path) if result_frame_path else None
    handoff_json = output_dir / "sql_persistence_handoff.json"
    handoff_report = output_dir / "sql_persistence_handoff_report.md"
    if handoff_ref is None and artifact_json.exists():
        _ensure_context_import_path(root)
        from context.sql_persistence_handoff_contract import default_handoff_ref, read_json_mapping
        artifact_result = read_json_mapping(artifact_json)
        contract_path_value = artifact_contract_path or artifact_result.get("artifact_contract_path")
        artifact_contract = read_json_mapping(contract_path_value) if contract_path_value else {}
        handoff_ref = default_handoff_ref(
            artifact_ref=str(artifact_contract.get("artifact_ref", "artifact:unknown")),
            sql_ref=str(artifact_result.get("sql_ref", artifact_contract.get("sql_ref", "sql:unknown"))),
        )
    handoff_ref = handoff_ref or "sql-handoff:pending-artifact-vector-indexing"
    return SqlPersistenceHandoffPlan(
        repository_root=root,
        artifact_json=artifact_json,
        artifact_contract_path=artifact_contract_path,
        result_frame_path=result_frame_path,
        output_dir=output_dir,
        handoff_json=handoff_json,
        handoff_report=handoff_report,
        handoff_ref=handoff_ref,
        execute=execute,
        surfaces=(
            SqlHandoffSurface(
                key="sql_persistence_handoff_contract",
                path=root / "src" / "context" / "sql_persistence_handoff_contract.py",
                reason="pure handoff contract from 0148",
                required=True,
            ),
            SqlHandoffSurface(
                key="artifact_result_json",
                path=artifact_json,
                reason="artifact vector indexing result from 0145/0147",
                required=True,
            ),
            SqlHandoffSurface(
                key="sql_context_store",
                path=root / "src" / "context" / "sql_context_store.py",
                reason="existing durable SQL authority; not imported by 0148 smoke",
                required=False,
            ),
        ),
    )


def execute_sql_persistence_handoff_plan(plan: SqlPersistenceHandoffPlan) -> int:
    if not plan.ready:
        for surface in plan.surfaces:
            if surface.required and not surface.path.exists():
                print(f"missing required surface: {surface.path}", file=sys.stderr)
        return 2
    _ensure_context_import_path(plan.repository_root)
    from context.sql_persistence_handoff_contract import build_sql_persistence_handoff_contract, read_json_mapping

    artifact_result = read_json_mapping(plan.artifact_json)
    contract_path = plan.artifact_contract_path or Path(str(artifact_result.get("artifact_contract_path")))
    artifact_contract = read_json_mapping(contract_path)
    frame_path = plan.result_frame_path or Path(str(artifact_result.get("result_frame_path")))
    result_frame_payload = _read_result_frame_payload(frame_path) if frame_path.exists() else {}
    contract = build_sql_persistence_handoff_contract(
        handoff_ref=plan.handoff_ref,
        artifact_result=artifact_result,
        artifact_contract=artifact_contract,
        result_frame_payload=result_frame_payload,
    )
    plan.output_dir.mkdir(parents=True, exist_ok=True)
    plan.handoff_json.write_text(json.dumps(contract.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = _handoff_report_markdown(plan, contract.to_mapping())
    plan.handoff_report.write_text(report, encoding="utf-8")
    print("==> sql_persistence_handoff")
    print(report, end="")
    return 0


def _read_result_frame_payload(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return {}
    payload = loaded.get("payload")
    if isinstance(payload, dict):
        return payload
    return loaded


def _handoff_report_markdown(plan: SqlPersistenceHandoffPlan, mapping: Mapping[str, Any]) -> str:
    return "\n".join([
        "# SQL persistence handoff result",
        "",
        f"handoff_json: `{plan.handoff_json}`",
        f"handoff_report: `{plan.handoff_report}`",
        f"handoff_ref: `{mapping['handoff_ref']}`",
        f"sql_ref: `{mapping['sql_ref']}`",
        f"artifact_ref: `{mapping['artifact_ref']}`",
        f"status: `{mapping['status']}`",
        f"point_id: `{mapping['point_id']}`",
        f"qdrant_rest_id: `{mapping['qdrant_rest_id']}`",
        f"vector_json: `{mapping['vector_json']}`",
        f"machine_vector_handoff: `{str(mapping['machine_vector_handoff']).lower()}`",
        f"strict_vector_handoff: `{str(mapping['strict_vector_handoff']).lower()}`",
        f"persistence_mode: `{mapping['persistence_mode']}`",
        f"durable_authority: `{mapping['durable_authority']}`",
        f"qdrant_role: `{mapping['qdrant_role']}`",
        "boundary: `handoff-only SQL envelope; no SQL write performed in 0148`",
        "",
    ])


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a SQL persistence handoff envelope from a local artifact vector result.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--artifact-json", type=Path, default=Path(DEFAULT_ARTIFACT_JSON))
    parser.add_argument("--artifact-contract", type=Path, default=None)
    parser.add_argument("--result-frame", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--handoff-ref", default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = build_sql_persistence_handoff_plan(
        args.repository_root,
        artifact_json=args.artifact_json,
        artifact_contract_path=args.artifact_contract,
        result_frame_path=args.result_frame,
        output_dir=args.output_dir,
        handoff_ref=args.handoff_ref,
        execute=args.execute,
    )
    if args.format == "json":
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))
    else:
        print(plan.to_markdown(), end="")
    if not args.execute:
        return 0 if plan.ready else 2
    return execute_sql_persistence_handoff_plan(plan)


def _ensure_context_import_path(root: Path) -> None:
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _resolve_repo_path(root: Path, path: Path | None) -> Path:
    if path is None:
        raise ValueError("path cannot be None")
    path = path.expanduser()
    if path.is_absolute():
        return path
    return root / path


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
