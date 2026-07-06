#!/usr/bin/env python3
"""Audit SQLContextStore write surface from a 0149 persistence record.

0150 is intentionally audit-only. It consumes the 0149 persistence record,
inspects the existing SQLContextStore class, and reports whether a later patch
can bind an explicit write method. It does not import backend clients and does
not perform a database write.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

DEFAULT_PERSISTENCE_JSON = ".var/smoke/artifacts/0149/sql_context_store_persistence_record.json"
DEFAULT_OUTPUT_DIR = ".var/smoke/artifacts/0150"


@dataclass(frozen=True, slots=True)
class SqlContextStoreWriteSurfaceAuditSurface:
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
class SqlContextStoreWriteSurfaceAuditPlan:
    repository_root: Path
    persistence_json: Path
    output_dir: Path
    audit_json: Path
    audit_report: Path
    requested_write_method: str | None
    execute: bool
    surfaces: tuple[SqlContextStoreWriteSurfaceAuditSurface, ...]

    @property
    def ready(self) -> bool:
        return all(surface.path.exists() for surface in self.surfaces if surface.required)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "persistence_json": str(self.persistence_json),
            "output_dir": str(self.output_dir),
            "audit_json": str(self.audit_json),
            "audit_report": str(self.audit_report),
            "requested_write_method": self.requested_write_method,
            "ready_for_sql_context_store_write_surface_audit": self.ready,
            "execute": self.execute,
            "surfaces": [surface.to_mapping(root=self.repository_root) for surface in self.surfaces],
            "boundary": "audit-only SQLContextStore write surface check; no backend write in 0150",
        }

    def to_markdown(self) -> str:
        lines = [
            "# SQLContextStore write surface audit plan",
            "",
            f"repository_root: `{self.repository_root}`",
            f"persistence_json: `{self.persistence_json}`",
            f"output_dir: `{self.output_dir}`",
            f"audit_json: `{self.audit_json}`",
            f"audit_report: `{self.audit_report}`",
            f"requested_write_method: `{self.requested_write_method}`",
            f"ready_for_sql_context_store_write_surface_audit: `{str(self.ready).lower()}`",
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
            "- consumes sql_context_store_persistence_record.json from 0149",
            "- reuses src/context/sql_context_store.py as the existing durable authority surface",
            "- reuses src/context/sql_context_store_write_surface_contract.py as a pure audit contract",
            "- writes sql_context_store_write_surface_audit.json and sql_context_store_write_surface_report.md only",
            "- does not create SQLPersistenceWorker",
            "- does not create SQLOrchestrator",
            "- does not create backend-specific SQL clients",
            "- does not import OpenVINO or Qdrant backends",
            "- does not modify the Scheduler run loop",
            "- Qdrant identifiers stay projection metadata; SQL remains durable authority",
        ])
        return "\n".join(lines) + "\n"


def build_sql_context_store_write_surface_audit_plan(
    root: Path,
    *,
    persistence_json: Path,
    output_dir: Path,
    requested_write_method: str | None,
    execute: bool,
) -> SqlContextStoreWriteSurfaceAuditPlan:
    root = root.resolve()
    persistence_json = _resolve_repo_path(root, persistence_json)
    output_dir = _resolve_repo_path(root, output_dir)
    return SqlContextStoreWriteSurfaceAuditPlan(
        repository_root=root,
        persistence_json=persistence_json,
        output_dir=output_dir,
        audit_json=output_dir / "sql_context_store_write_surface_audit.json",
        audit_report=output_dir / "sql_context_store_write_surface_report.md",
        requested_write_method=requested_write_method,
        execute=execute,
        surfaces=(
            SqlContextStoreWriteSurfaceAuditSurface(
                key="sql_context_store",
                path=root / "src" / "context" / "sql_context_store.py",
                reason="existing durable SQL authority surface",
                required=True,
            ),
            SqlContextStoreWriteSurfaceAuditSurface(
                key="sql_context_store_persistence_record",
                path=persistence_json,
                reason="record produced by 0149",
                required=True,
            ),
            SqlContextStoreWriteSurfaceAuditSurface(
                key="sql_context_store_write_surface_contract",
                path=root / "src" / "context" / "sql_context_store_write_surface_contract.py",
                reason="pure write-surface audit contract from 0150",
                required=True,
            ),
        ),
    )


def execute_sql_context_store_write_surface_audit_plan(plan: SqlContextStoreWriteSurfaceAuditPlan) -> int:
    if not plan.ready:
        for surface in plan.surfaces:
            if surface.required and not surface.path.exists():
                print(f"missing required surface: {surface.path}", file=sys.stderr)
        return 2

    _ensure_context_import_path(plan.repository_root)
    from context.sql_context_store_write_surface_contract import (
        build_sql_context_store_write_surface_record,
        inspect_sql_context_store_write_surface,
        read_json_mapping,
    )

    persistence_record = read_json_mapping(plan.persistence_json)
    surface_audit = inspect_sql_context_store_write_surface(
        plan.repository_root,
        requested_write_method=plan.requested_write_method,
    )
    record = build_sql_context_store_write_surface_record(
        persistence_record=persistence_record,
        surface_audit=surface_audit,
    )
    mapping = record.to_mapping()
    plan.output_dir.mkdir(parents=True, exist_ok=True)
    plan.audit_json.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = _audit_report_markdown(plan, mapping)
    plan.audit_report.write_text(report, encoding="utf-8")
    print("==> sql_context_store_write_surface_audit")
    print(report, end="")
    return 0


def _audit_report_markdown(plan: SqlContextStoreWriteSurfaceAuditPlan, mapping: Mapping[str, Any]) -> str:
    audit = mapping["surface_audit"]
    method_names = [method["name"] for method in audit.get("method_signatures", [])]
    lines = [
        "# SQLContextStore write surface audit result",
        "",
        f"audit_json: `{plan.audit_json}`",
        f"audit_report: `{plan.audit_report}`",
        f"audit_ref: `{mapping['audit_ref']}`",
        f"persistence_ref: `{mapping['persistence_ref']}`",
        f"sql_ref: `{mapping['sql_ref']}`",
        f"artifact_ref: `{mapping['artifact_ref']}`",
        f"durable_authority: `{mapping['durable_authority']}`",
        f"qdrant_role: `{mapping['qdrant_role']}`",
        f"write_attempted: `{str(mapping['write_attempted']).lower()}`",
        f"write_status: `{mapping['write_status']}`",
        f"selected_write_method: `{mapping['selected_write_method']}`",
        f"ready_for_controlled_write_patch: `{str(audit.get('ready_for_controlled_write_patch')).lower()}`",
        f"recommended_next_patch: `{mapping['recommended_next_patch']}`",
        f"gap_reason: `{audit.get('gap_reason')}`",
        f"sql_context_store_exists: `{str(audit.get('exists')).lower()}`",
        f"has_sql_context_store_class: `{str(audit.get('has_sql_context_store_class')).lower()}`",
        f"method_count: `{len(method_names)}`",
        "",
        "## SQLContextStore methods",
        "",
    ]
    if method_names:
        for method_name in method_names:
            lines.append(f"- `{method_name}`")
    else:
        lines.append("- none detected")
    lines.extend([
        "",
        "boundary: `0150 audits the existing SQLContextStore write surface only; no backend write is performed`",
        "",
    ])
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the existing SQLContextStore write surface from a 0149 persistence record.")
    parser.add_argument("repository_root", type=Path)
    parser.add_argument("--persistence-json", type=Path, default=Path(DEFAULT_PERSISTENCE_JSON))
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--write-method", default=None, help="Require a specific existing SQLContextStore method name for the next controlled write patch.")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = build_sql_context_store_write_surface_audit_plan(
        args.repository_root,
        persistence_json=args.persistence_json,
        output_dir=args.output_dir,
        requested_write_method=args.write_method,
        execute=args.execute,
    )
    if args.format == "json":
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))
    else:
        print(plan.to_markdown(), end="")
    if not args.execute:
        return 0 if plan.ready else 2
    return execute_sql_context_store_write_surface_audit_plan(plan)


def _ensure_context_import_path(root: Path) -> None:
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _resolve_repo_path(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
