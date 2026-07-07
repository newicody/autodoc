#!/usr/bin/env python3
"""Audit context recall integration readiness after Bloc F projection acceptance.

0213 is the Bloc G context recall integration audit only.

It reads controlled_sql_qdrant_projection_acceptance.json from 0212, scans
existing repository surfaces by safe text/AST file reads, and writes
context_recall_integration_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0213 must audit existing context, recall, sql_ref, rehydrate, and response
artifact surfaces before any context recall integration plan or execution is
allowed.

0213 does not execute recall.
0213 does not query Qdrant.
0213 does not read SQL records.
0213 does not write SQL.
0213 does not write Qdrant.
0213 does not add a new SQL backend.
0213 does not add a new Qdrant backend.
0213 does not add a new inference path.
0213 does not rewrite runtime history.
0213 does not execute Scheduler.run.
0213 does not modify Scheduler.run.
0213 does not import runtime handler modules.
0213 does not call handle_scheduler_route_command.
0213 does not call handle_scheduler_route_request.
0213 does not call prepare_route_proxy_runtime.
0213 does not call read_route_frame.
0213 does not request writer permits.
0213 does not call write_route_frame.
0213 does not write ControlProxy or RouteProxy frames.
0213 does not call GitHub API or use network.

Bloc G target path is context/query -> Qdrant recall -> sql_ref -> SQL rehydrate
-> response artifact.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Mapping


CONTEXT_RECALL_INTEGRATION_AUDIT_SCHEMA = "missipy.context_recall.integration_audit.v1"
EXPECTED_ACCEPTANCE_SCHEMA = "missipy.sql_qdrant.controlled_projection_acceptance.v1"
DEFAULT_OUTPUT_NAME = "context_recall_integration_audit.json"

SCAN_ROOTS = ("src", "tools", "doc")
SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".var", "patch"}
TEXT_SUFFIXES = {".py", ".md", ".dot", ".json", ".jsonl", ".txt"}

CONTEXT_TOKENS = (
    "context",
    "Context",
    "artifact",
    "query",
)
RECALL_TOKENS = (
    "recall",
    "Qdrant",
    "qdrant",
    "vector",
    "collection",
)
REHYDRATE_TOKENS = (
    "rehydrate",
    "sql_ref",
    "get_record",
    "DbApiSqlContextStore",
)
RESPONSE_TOKENS = (
    "response",
    "result",
    "artifact",
    "to_mapping",
)
PROJECTION_TOKENS = (
    "controlled_sql_qdrant_projection_acceptance",
    "qdrant_payload",
    "sql_ref",
)

FALSE_ACCEPTANCE_FLAGS = (
    "sql_write_allowed_by_0212",
    "qdrant_write_allowed_by_0212",
    "sql_written_by_0212",
    "qdrant_written_by_0212",
    "runtime_imports_executed_by_0212",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0212",
    "routeproxy_prepared_by_0212",
    "read_route_frame_called_by_0212",
    "writer_permits_requested_by_0212",
    "frames_written_by_0212",
    "controlproxy_frames_written_by_0212",
    "eventbus_instantiated_by_0212",
    "network_used_by_0212",
    "runtime_history_rewritten_by_0212",
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


class ContextRecallIntegrationAuditError(ValueError):
    """Raised when context recall integration audit input is unsafe."""


def audit_context_recall_integration(
    *,
    projection_acceptance_path: Path | str,
    repo_root: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Audit context recall integration readiness without recall execution."""

    acceptance_path = Path(projection_acceptance_path)
    root = Path(repo_root)
    acceptance = _read_json_file(acceptance_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_projection_acceptance(acceptance, issues, warnings)

    if not root.exists():
        issues.append("repo_root must exist")
    if not root.is_dir():
        issues.append("repo_root must be a directory")

    target_runtime_root = Path(str(acceptance.get("target_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be context_recall_integration_audit.json")

    surface_reports = _scan_repository_surfaces(root)
    context_surfaces = _matching_reports(surface_reports, CONTEXT_TOKENS)
    recall_surfaces = _matching_reports(surface_reports, RECALL_TOKENS)
    rehydrate_surfaces = _matching_reports(surface_reports, REHYDRATE_TOKENS)
    response_surfaces = _matching_reports(surface_reports, RESPONSE_TOKENS)
    projection_surfaces = _matching_reports(surface_reports, PROJECTION_TOKENS)

    if not context_surfaces:
        issues.append("no existing context/query surface found")
    if not recall_surfaces:
        issues.append("no existing recall/Qdrant surface found")
    if not rehydrate_surfaces:
        issues.append("no existing sql_ref rehydrate surface found")
    if not response_surfaces:
        issues.append("no existing response/result artifact surface found")
    if not projection_surfaces:
        issues.append("no existing projection acceptance/sql_ref surface found")

    audit = {
        "schema": CONTEXT_RECALL_INTEGRATION_AUDIT_SCHEMA,
        "bloc": "G",
        "bloc_name": "context-recall-integration",
        "projection_acceptance_path": str(acceptance_path),
        "projection_acceptance_schema": acceptance.get("schema"),
        "accepted_baseline": acceptance.get("accepted_baseline"),
        "projection_digest": acceptance.get("projection_digest"),
        "sql_ref": acceptance.get("sql_ref"),
        "qdrant_payload": acceptance.get("qdrant_payload"),
        "source_entry_digest": acceptance.get("source_entry_digest"),
        "repair_digest": acceptance.get("repair_digest"),
        "target_runtime_root": acceptance.get("target_runtime_root"),
        "target_isolated_runtime_root": acceptance.get("target_isolated_runtime_root"),
        "repo_root": str(root),
        "scan_roots": list(SCAN_ROOTS),
        "surface_count": len(surface_reports),
        "context_surface_count": len(context_surfaces),
        "recall_surface_count": len(recall_surfaces),
        "rehydrate_surface_count": len(rehydrate_surfaces),
        "response_surface_count": len(response_surfaces),
        "projection_surface_count": len(projection_surfaces),
        "surface_reports": surface_reports,
        "context_surfaces": context_surfaces,
        "recall_surfaces": recall_surfaces,
        "rehydrate_surfaces": rehydrate_surfaces,
        "response_surfaces": response_surfaces,
        "projection_surfaces": projection_surfaces,
        "context_recall_integration_audit_success": not issues,
        "context_recall_integration_plan_allowed_next": not issues,
        "planned_next_patch": "0214-context_recall_integration_plan",
        "integration_contract": {
            "input": "context/query artifact",
            "recall": "Qdrant recall returns sql_ref",
            "rehydration": "SQL authority hydrates sql_ref",
            "output": "response/result artifact",
            "authority": "SQL remains durable authority",
            "projection": "Qdrant remains projection/search/recall only",
        },
        "target_path": "context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact",
        "readiness_decisions": [
            "Reuse existing context/query surfaces before new code.",
            "Reuse existing Qdrant recall surfaces before new code.",
            "Reuse existing sql_ref rehydrate surfaces before new code.",
            "Do not execute recall in P0213.",
            "Do not read SQL records in P0213.",
            "Do not write SQL/Qdrant in P0213.",
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
        "runtime_imports_executed_by_0213": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0213": False,
        "routeproxy_prepared_by_0213": False,
        "read_route_frame_called_by_0213": False,
        "writer_permits_requested_by_0213": False,
        "frames_written_by_0213": False,
        "controlproxy_frames_written_by_0213": False,
        "eventbus_instantiated_by_0213": False,
        "network_used_by_0213": False,
        "sql_record_read_by_0213": False,
        "qdrant_queried_by_0213": False,
        "recall_executed_by_0213": False,
        "sql_written_by_0213": False,
        "qdrant_written_by_0213": False,
    }

    if output_path is not None:
        _write_audit(final_output, audit)

    return audit


def _audit_projection_acceptance(
    acceptance: Mapping[str, Any],
    issues: list[str],
    warnings: list[str],
) -> None:
    if acceptance.get("schema") != EXPECTED_ACCEPTANCE_SCHEMA:
        issues.append("P0212 controlled SQL/Qdrant projection acceptance schema mismatch")
    if acceptance.get("controlled_sql_qdrant_projection_accepted") is not True:
        issues.append("controlled_sql_qdrant_projection_accepted must be true")
    if acceptance.get("sql_qdrant_projection_contract_accepted") is not True:
        issues.append("sql_qdrant_projection_contract_accepted must be true")
    if acceptance.get("bloc_f_complete") is not True:
        issues.append("bloc_f_complete must be true")
    if acceptance.get("next_bloc") != "G":
        issues.append("next_bloc must be G")
    if acceptance.get("issues") not in ([], None):
        issues.append("P0212 controlled SQL/Qdrant projection acceptance issues must be empty")
    if isinstance(acceptance.get("warnings"), list) and acceptance.get("warnings"):
        warnings.extend(str(item) for item in acceptance.get("warnings", []))
    if not isinstance(acceptance.get("sql_ref"), str) or not acceptance.get("sql_ref"):
        issues.append("sql_ref must be present")
    payload = acceptance.get("qdrant_payload")
    if not isinstance(payload, Mapping):
        issues.append("qdrant_payload must be present")
    elif payload.get("sql_ref") != acceptance.get("sql_ref"):
        issues.append("qdrant_payload.sql_ref must match sql_ref")
    if acceptance.get("payload_contains_sql_ref") is not True:
        issues.append("payload_contains_sql_ref must be true")
    if acceptance.get("rehydration_required") is not True:
        issues.append("rehydration_required must be true")
    if not isinstance(acceptance.get("projection_digest"), str) or not acceptance.get("projection_digest"):
        issues.append("projection_digest must be present")
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
            all_tokens = set(CONTEXT_TOKENS + RECALL_TOKENS + REHYDRATE_TOKENS + RESPONSE_TOKENS + PROJECTION_TOKENS)
            matched_tokens = sorted(token for token in all_tokens if token in text)
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
    token_set = set(tokens)
    matches: list[dict[str, Any]] = []
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
        raise ContextRecallIntegrationAuditError("input must be a JSON object")
    return raw


def _write_audit(path: Path, audit: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ContextRecallIntegrationAuditError(
            "output filename must be context_recall_integration_audit.json"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit context recall integration readiness.")
    parser.add_argument("--projection-acceptance", required=True, help="Path to controlled_sql_qdrant_projection_acceptance.json.")
    parser.add_argument("--repo-root", default=".", help="Repository root to scan.")
    parser.add_argument("--output", help="Optional context_recall_integration_audit.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    audit = audit_context_recall_integration(
        projection_acceptance_path=Path(args.projection_acceptance),
        repo_root=Path(args.repo_root),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(f"context_recall_integration_audit_success: {audit['context_recall_integration_audit_success']}")
        print(f"context_recall_integration_plan_allowed_next: {audit['context_recall_integration_plan_allowed_next']}")
        print(f"context_surface_count: {audit['context_surface_count']}")
        print(f"recall_surface_count: {audit['recall_surface_count']}")
        print(f"rehydrate_surface_count: {audit['rehydrate_surface_count']}")
        print(f"response_surface_count: {audit['response_surface_count']}")
        print(f"planned_next_patch: {audit['planned_next_patch']}")
        print(f"issues: {len(audit['issues'])}")
        print(f"warnings: {len(audit['warnings'])}")
    return 0 if audit["context_recall_integration_audit_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
