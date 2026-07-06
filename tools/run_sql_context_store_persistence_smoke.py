#!/usr/bin/env python3
"""Prepare a SQLContextStore persistence record from a SQL handoff envelope.

0149 connects the 0148 handoff to the existing SQLContextStore authority surface
as a structured record. It does not create a worker, does not use backend-specific
SQL clients, and does not call OpenVINO or Qdrant.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

DEFAULT_HANDOFF_JSON = ".var/smoke/artifacts/0148/sql_persistence_handoff.json"
DEFAULT_OUTPUT_DIR = ".var/smoke/artifacts/0149"


@dataclass(frozen=True, slots=True)
class SqlContextStorePersistenceSurface:
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
class SqlContextStorePersistencePlan:
    repository_root: Path
    handoff_json: Path
    output_dir: Path
    persistence_json: Path
    persistence_report: Path
    persistence_ref: str
    execute: bool
    surfaces: tuple[SqlContextStorePersistenceSurface, ...]

    @property
    def ready(self) -> bool:
        return self.handoff_json.exists() and all(
            surface.path.exists() for surface in self.surfaces if surface.required
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "handoff_json": str(self.handoff_json),
            "output_dir": str(self.output_dir),
            "persistence_json": str(self.persistence_json),
            "persistence_report": str(self.persistence_report),
            "persistence_ref": self.persistence_ref,
            "ready_for_sql_context_store_persistence_smoke": self.ready,
            "execute": self.execute,
            "surfaces": [surface.to_mapping(root=self.repository_root) for surface in self.surfaces],
            "boundary": "record-only SQLContextStore persistence smoke; no database-specific write in 0149",
        }

    def to_markdown(self) -> str:
        lines = [
            "# SQLContextStore persistence smoke plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"handoff_json: `{self.handoff_json}`",
            f"output_dir: `{self.output_dir}`",
            f"persistence_json: `{self.persistence_json}`",
            f"persistence_report: `{self.persistence_report}`",
            f"persistence_ref: `{self.persistence_ref}`",
            f"ready_for_sql_context_store_persistence_smoke: `{str(self.ready).lower()}`",
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
            "- consumes sql_persistence_handoff.json from 0148",
            "- reuses src/context/sql_context_store.py as the existing durable authority surface",
            "- reuses src/context/sql_context_store_persistence_contract.py as a pure record contract",
            "- writes sql_context_store_persistence_record.json and sql_context_store_persistence_report.md only",
            "- does not create SQLPersistenceWorker",
            "- does not create SQLOrchestrator",
            "- does not create LocalArtifactOrchestrator",
            "- does not create LocalVectorIndexingOrchestrator",
            "- does not import backend clients",
            "- Qdrant identifiers stay projection metadata; SQL remains durable authority",
        ])
        return "\n".join(lines) + "\n"


def build_sql_context_store_persistence_plan(
    root: Path,
    *,
    handoff_json: Path,
    output_dir: Path,
    persistence_ref: str | None,
    execute: bool,
) -> SqlContextStorePersistencePlan:
    root = root.resolve()
    handoff_json = _resolve_repo_path(root, handoff_json)
    output_dir = _resolve_repo_path(root, output_dir)
    persistence_json = output_dir / "sql_context_store_persistence_record.json"
    persistence_report = output_dir / "sql_context_store_persistence_report.md"
    if persistence_ref is None and handoff_json.exists():
        _ensure_context_import_path(root)
        from context.sql_context_store_persistence_contract import default_persistence_ref, read_json_mapping
        handoff = read_json_mapping(handoff_json)
        persistence_ref = default_persistence_ref(
            handoff_ref=str(handoff.get("handoff_ref", "sql-handoff:unknown")),
            sql_ref=str(handoff.get("sql_ref", "sql:unknown")),
        )
    persistence_ref = persistence_ref or "sql-context-persist:pending-sql-handoff"
    return SqlContextStorePersistencePlan(
        repository_root=root,
        handoff_json=handoff_json,
        output_dir=output_dir,
        persistence_json=persistence_json,
        persistence_report=persistence_report,
        persistence_ref=persistence_ref,
        execute=execute,
        surfaces=(
            SqlContextStorePersistenceSurface(
                key="sql_context_store",
                path=root / "src" / "context" / "sql_context_store.py",
                reason="existing durable SQL authority surface",
                required=True,
            ),
            SqlContextStorePersistenceSurface(
                key="sql_persistence_handoff_json",
                path=handoff_json,
                reason="handoff envelope from 0148",
                required=True,
            ),
            SqlContextStorePersistenceSurface(
                key="sql_context_store_persistence_contract",
                path=root / "src" / "context" / "sql_context_store_persistence_contract.py",
                reason="pure persistence record contract from 0149",
                required=True,
            ),
        ),
    )


def execute_sql_context_store_persistence_plan(plan: SqlContextStorePersistencePlan) -> int:
    if not plan.ready:
        for surface in plan.surfaces:
            if surface.required and not surface.path.exists():
                print(f"missing required surface: {surface.path}", file=sys.stderr)
        return 2
    _ensure_context_import_path(plan.repository_root)
    from context.sql_context_store_persistence_contract import (
        build_sql_context_store_persistence_record,
        inspect_sql_context_store_surface,
        read_json_mapping,
    )

    handoff = read_json_mapping(plan.handoff_json)
    surface = inspect_sql_context_store_surface(plan.repository_root)
    record = build_sql_context_store_persistence_record(
        handoff=handoff,
        sql_context_store_surface=surface,
        persistence_ref=plan.persistence_ref,
    )
    mapping = record.to_mapping()
    plan.output_dir.mkdir(parents=True, exist_ok=True)
    plan.persistence_json.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = _persistence_report_markdown(plan, mapping)
    plan.persistence_report.write_text(report, encoding="utf-8")
    print("==> sql_context_store_persistence")
    print(report, end="")
    return 0


def _persistence_report_markdown(plan: SqlContextStorePersistencePlan, mapping: Mapping[str, Any]) -> str:
    surface = mapping["sql_context_store_surface"]
    return "\n".join([
        "# SQLContextStore persistence smoke result",
        "",
        f"persistence_json: `{plan.persistence_json}`",
        f"persistence_report: `{plan.persistence_report}`",
        f"persistence_ref: `{mapping['persistence_ref']}`",
        f"handoff_ref: `{mapping['handoff_ref']}`",
        f"sql_ref: `{mapping['sql_ref']}`",
        f"artifact_ref: `{mapping['artifact_ref']}`",
        f"status: `{mapping['status']}`",
        f"point_id: `{mapping['point_id']}`",
        f"qdrant_rest_id: `{mapping['qdrant_rest_id']}`",
        f"machine_vector_handoff: `{str(mapping['machine_vector_handoff']).lower()}`",
        f"strict_vector_handoff: `{str(mapping['strict_vector_handoff']).lower()}`",
        f"persistence_mode: `{mapping['persistence_mode']}`",
        f"durable_authority: `{mapping['durable_authority']}`",
        f"qdrant_role: `{mapping['qdrant_role']}`",
        f"sql_context_store_exists: `{str(surface.get('exists')).lower()}`",
        f"sql_context_store_symbol: `{str(surface.get('has_sql_context_store')).lower()}`",
        f"selected_write_method: `{surface.get('selected_write_method')}`",
        "write_status: `record_only`",
        "boundary: `SQLContextStore persistence record prepared; no backend-specific write performed in 0149`",
        "",
    ]) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a SQLContextStore persistence record from a 0148 SQL handoff.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--handoff-json", type=Path, default=Path(DEFAULT_HANDOFF_JSON))
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--persistence-ref", default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = build_sql_context_store_persistence_plan(
        args.repository_root,
        handoff_json=args.handoff_json,
        output_dir=args.output_dir,
        persistence_ref=args.persistence_ref,
        execute=args.execute,
    )
    if args.format == "json":
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))
    else:
        print(plan.to_markdown(), end="")
    if not args.execute:
        return 0 if plan.ready else 2
    return execute_sql_context_store_persistence_plan(plan)


def _ensure_context_import_path(root: Path) -> None:
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _resolve_repo_path(root: Path, path: Path) -> Path:
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
