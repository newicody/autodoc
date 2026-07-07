#!/usr/bin/env python3
"""Audit SQL/Qdrant projection readiness after forward-only provenance repair.

0210 is the Bloc F SQL/Qdrant projection readiness audit only.

It reads provenance_repair_acceptance.json from 0209, scans existing repository
surfaces by text/AST-safe file reads, and writes
sql_qdrant_projection_readiness_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0210 must audit existing SQL and Qdrant projection surfaces before any SQL/Qdrant
projection plan or write is allowed.

0210 does not write SQL.
0210 does not write Qdrant.
0210 does not add a new SQL backend.
0210 does not add a new Qdrant backend.
0210 does not rewrite runtime history.
0210 does not execute Scheduler.run.
0210 does not modify Scheduler.run.
0210 does not import runtime handler modules.
0210 does not call handle_scheduler_route_command.
0210 does not call handle_scheduler_route_request.
0210 does not call prepare_route_proxy_runtime.
0210 does not call read_route_frame.
0210 does not request writer permits.
0210 does not call write_route_frame.
0210 does not write ControlProxy or RouteProxy frames.
0210 does not call GitHub API or use network.

SQL remains durable authority.
Qdrant remains projection/search/recall only.
Qdrant payloads must carry sql_ref and rehydrate from SQL.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Mapping


SQL_QDRANT_PROJECTION_READINESS_AUDIT_SCHEMA = (
    "missipy.sql_qdrant.projection_readiness_audit.v1"
)
EXPECTED_ACCEPTANCE_SCHEMA = "missipy.provenance.forward_only_repair_acceptance.v1"
DEFAULT_OUTPUT_NAME = "sql_qdrant_projection_readiness_audit.json"

SCAN_ROOTS = ("src", "tools", "doc")
SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".var", "patch"}
TEXT_SUFFIXES = {".py", ".md", ".dot", ".json", ".jsonl", ".txt"}

SQL_TOKENS = (
    "DbApiSqlContextStore",
    "sql_ref",
    "SQL",
    "sqlite",
    "postgres",
)
QDRANT_TOKENS = (
    "Qdrant",
    "qdrant",
    "collection",
    "vector",
)
REHYDRATE_TOKENS = (
    "rehydrate",
    "sql_ref",
    "get_record",
)
PROVENANCE_TOKENS = (
    "provenance_repair_acceptance",
    "source_baseline_ref",
    "source_entry_digest",
)

FALSE_ACCEPTANCE_FLAGS = (
    "runtime_history_rewritten_by_0209",
    "source_artifact_rewritten_by_0209",
    "sql_write_allowed_by_0209",
    "qdrant_write_allowed_by_0209",
    "sql_written_by_0209",
    "qdrant_written_by_0209",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0209",
    "routeproxy_prepared_by_0209",
    "mark_route_frame_stale_called_by_0209",
    "read_route_frame_called_by_0209",
    "writer_permits_requested_by_0209",
    "frames_written_by_0209",
    "controlproxy_frames_written_by_0209",
    "eventbus_instantiated_by_0209",
    "network_used_by_0209",
)

FALSE_NEW_SURFACE_FLAGS = (
    "new_runtime_handler_added",
    "new_adapter_added",
    "new_bus_added",
    "new_scheduler_added",
    "new_controlproxy_runtime_added",
    "new_routeproxy_runtime_added",
    "new_sql_backend_added",
    "new_qdrant_backend_added",
    "new_github_client_added",
    "new_graph_renderer_added",
    "new_inference_path_added",
)


class SqlQdrantProjectionReadinessAuditError(ValueError):
    """Raised when SQL/Qdrant projection readiness audit input is unsafe."""


def audit_sql_qdrant_projection_readiness(
    *,
    provenance_repair_acceptance_path: Path | str,
    repo_root: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Audit SQL/Qdrant projection readiness without writes or imports."""

    acceptance_path = Path(provenance_repair_acceptance_path)
    root = Path(repo_root)
    acceptance = _read_json_file(acceptance_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_provenance_acceptance(acceptance, issues, warnings)

    if not root.exists():
        issues.append("repo_root must exist")
    if not root.is_dir():
        issues.append("repo_root must be a directory")

    target_runtime_root = Path(str(acceptance.get("target_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be sql_qdrant_projection_readiness_audit.json")

    surface_reports = _scan_repository_surfaces(root)
    sql_surfaces = _matching_reports(surface_reports, SQL_TOKENS)
    qdrant_surfaces = _matching_reports(surface_reports, QDRANT_TOKENS)
    rehydrate_surfaces = _matching_reports(surface_reports, REHYDRATE_TOKENS)
    provenance_surfaces = _matching_reports(surface_reports, PROVENANCE_TOKENS)

    if not sql_surfaces:
        issues.append("no existing SQL/sql_ref surface found")
    if not qdrant_surfaces:
        issues.append("no existing Qdrant/vector surface found")
    if not rehydrate_surfaces:
        issues.append("no existing SQL rehydrate/sql_ref surface found")
    if not provenance_surfaces:
        issues.append("no existing provenance repair surface found")

    readiness = {
        "schema": SQL_QDRANT_PROJECTION_READINESS_AUDIT_SCHEMA,
        "bloc": "F",
        "bloc_name": "sql-qdrant-projection-readiness",
        "provenance_repair_acceptance_path": str(acceptance_path),
        "provenance_repair_acceptance_schema": acceptance.get("schema"),
        "accepted_baseline": acceptance.get("accepted_baseline"),
        "source_baseline_ref": acceptance.get("source_baseline_ref"),
        "source_entry_digest": acceptance.get("source_entry_digest"),
        "repair_digest": acceptance.get("repair_digest"),
        "target_runtime_root": acceptance.get("target_runtime_root"),
        "target_isolated_runtime_root": acceptance.get("target_isolated_runtime_root"),
        "repo_root": str(root),
        "scan_roots": list(SCAN_ROOTS),
        "surface_count": len(surface_reports),
        "sql_surface_count": len(sql_surfaces),
        "qdrant_surface_count": len(qdrant_surfaces),
        "rehydrate_surface_count": len(rehydrate_surfaces),
        "provenance_surface_count": len(provenance_surfaces),
        "surface_reports": surface_reports,
        "sql_surfaces": sql_surfaces,
        "qdrant_surfaces": qdrant_surfaces,
        "rehydrate_surfaces": rehydrate_surfaces,
        "provenance_surfaces": provenance_surfaces,
        "sql_qdrant_projection_readiness_audit_success": not issues,
        "sql_qdrant_projection_plan_allowed_next": not issues,
        "planned_next_patch": "0211-sql_qdrant_projection_plan",
        "projection_contract": {
            "sql_role": "durable authority",
            "qdrant_role": "projection/search/recall only",
            "payload_contract": "Qdrant payloads carry sql_ref",
            "rehydration_contract": "hydrate returned sql_ref from SQL authority",
            "provenance_contract": "use forward-only provenance repair acceptance as chain repair proof",
        },
        "readiness_decisions": [
            "SQL remains durable authority.",
            "Qdrant remains projection/search/recall only.",
            "Qdrant payloads must carry sql_ref.",
            "Query results must be rehydrated from SQL.",
            "No SQL/Qdrant writes are allowed in P0210.",
        ],
        "issues": issues,
        "warnings": warnings,
        "existing_surfaces_reused": True,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_scheduler_added": False,
        "new_controlproxy_runtime_added": False,
        "new_routeproxy_runtime_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "new_graph_renderer_added": False,
        "new_inference_path_added": False,
        "runtime_imports_executed_by_0210": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0210": False,
        "routeproxy_prepared_by_0210": False,
        "read_route_frame_called_by_0210": False,
        "writer_permits_requested_by_0210": False,
        "frames_written_by_0210": False,
        "controlproxy_frames_written_by_0210": False,
        "eventbus_instantiated_by_0210": False,
        "network_used_by_0210": False,
        "sql_write_allowed_by_0210": False,
        "qdrant_write_allowed_by_0210": False,
        "sql_written_by_0210": False,
        "qdrant_written_by_0210": False,
    }

    if output_path is not None:
        _write_audit(final_output, readiness)

    return readiness


def _audit_provenance_acceptance(
    acceptance: Mapping[str, Any],
    issues: list[str],
    warnings: list[str],
) -> None:
    if acceptance.get("schema") != EXPECTED_ACCEPTANCE_SCHEMA:
        issues.append("P0209 provenance repair acceptance schema mismatch")
    if acceptance.get("forward_only_provenance_repair_accepted") is not True:
        issues.append("forward_only_provenance_repair_accepted must be true")
    if acceptance.get("provenance_repair_accepted") is not True:
        issues.append("provenance_repair_accepted must be true")
    if acceptance.get("bloc_e_complete") is not True:
        issues.append("bloc_e_complete must be true")
    if acceptance.get("next_bloc") != "F":
        issues.append("next_bloc must be F")
    if acceptance.get("issues") not in ([], None):
        issues.append("P0209 provenance repair acceptance issues must be empty")
    if isinstance(acceptance.get("warnings"), list) and acceptance.get("warnings"):
        warnings.extend(str(item) for item in acceptance.get("warnings", []))
    if not isinstance(acceptance.get("source_baseline_ref"), str) or not acceptance.get("source_baseline_ref"):
        issues.append("source_baseline_ref must be present")
    if not isinstance(acceptance.get("source_entry_digest"), str) or not acceptance.get("source_entry_digest"):
        issues.append("source_entry_digest must be present")
    if not isinstance(acceptance.get("repair_digest"), str) or not acceptance.get("repair_digest"):
        issues.append("repair_digest must be present")
    if acceptance.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for flag in FALSE_ACCEPTANCE_FLAGS:
        if acceptance.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if acceptance.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _scan_repository_surfaces(root: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for scan_root in SCAN_ROOTS:
        base = root / scan_root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix not in TEXT_SUFFIXES:
                continue
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            text = _read_text(path)
            if not text:
                continue
            relative = path.relative_to(root).as_posix()
            matched_tokens = sorted(
                token for token in set(SQL_TOKENS + QDRANT_TOKENS + REHYDRATE_TOKENS + PROVENANCE_TOKENS)
                if token in text
            )
            if not matched_tokens:
                continue
            functions: list[str] = []
            classes: list[str] = []
            parse_error = ""
            if path.suffix == ".py":
                try:
                    tree = ast.parse(text, filename=relative)
                except SyntaxError as exc:
                    parse_error = str(exc)
                else:
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            functions.append(node.name)
                        elif isinstance(node, ast.ClassDef):
                            classes.append(node.name)
            reports.append({
                "path": relative,
                "suffix": path.suffix,
                "matched_tokens": matched_tokens,
                "function_count": len(functions),
                "class_count": len(classes),
                "functions": sorted(functions),
                "classes": sorted(classes),
                "parse_error": parse_error,
                "use_before_new_code": True,
            })
    return reports


def _matching_reports(reports: list[Mapping[str, Any]], tokens: tuple[str, ...]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    token_set = set(tokens)
    for report in reports:
        matched = set(report.get("matched_tokens", []))
        if matched & token_set:
            matches.append({
                "path": str(report.get("path", "")),
                "matched_tokens": sorted(matched & token_set),
                "use_before_new_code": bool(report.get("use_before_new_code")),
            })
    return matches


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SqlQdrantProjectionReadinessAuditError("input must be a JSON object")
    return raw


def _write_audit(path: Path, audit: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise SqlQdrantProjectionReadinessAuditError(
            "output filename must be sql_qdrant_projection_readiness_audit.json"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit SQL/Qdrant projection readiness.")
    parser.add_argument("--provenance-repair-acceptance", required=True, help="Path to provenance_repair_acceptance.json.")
    parser.add_argument("--repo-root", default=".", help="Repository root to scan.")
    parser.add_argument("--output", help="Optional sql_qdrant_projection_readiness_audit.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    audit = audit_sql_qdrant_projection_readiness(
        provenance_repair_acceptance_path=Path(args.provenance_repair_acceptance),
        repo_root=Path(args.repo_root),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(f"sql_qdrant_projection_readiness_audit_success: {audit['sql_qdrant_projection_readiness_audit_success']}")
        print(f"sql_qdrant_projection_plan_allowed_next: {audit['sql_qdrant_projection_plan_allowed_next']}")
        print(f"sql_surface_count: {audit['sql_surface_count']}")
        print(f"qdrant_surface_count: {audit['qdrant_surface_count']}")
        print(f"rehydrate_surface_count: {audit['rehydrate_surface_count']}")
        print(f"planned_next_patch: {audit['planned_next_patch']}")
        print(f"issues: {len(audit['issues'])}")
        print(f"warnings: {len(audit['warnings'])}")
    return 0 if audit["sql_qdrant_projection_readiness_audit_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
