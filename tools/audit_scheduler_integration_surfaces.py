#!/usr/bin/env python3
"""Audit existing Scheduler integration surfaces after controlled dev smoke.

0201 is the Bloc C Scheduler integration surface audit only.

It reads controlled_dev_routeproxy_smoke_post_execution_acceptance.json from
0200, inspects existing source files by AST/text, and writes
scheduler_integration_surface_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0201 must audit existing code before any Scheduler hook plan is allowed.

0201 must not introduce a new runtime handler, adapter, bus, Scheduler,
RouteProxy runtime, ControlProxy runtime, SQL backend, Qdrant backend, GitHub
client, graph renderer, or inference path.

0201 does not execute Scheduler.run.
0201 does not import runtime handler modules.
0201 does not call handle_scheduler_route_command.
0201 does not call handle_scheduler_route_request.
0201 does not call prepare_route_proxy_runtime.
0201 does not call read_route_frame.
0201 does not request writer permits.
0201 does not call write_route_frame.
0201 does not write ControlProxy or RouteProxy frames.
0201 does not call GitHub API or use network.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Mapping


SCHEDULER_INTEGRATION_SURFACE_AUDIT_SCHEMA = "missipy.scheduler.integration_surface_audit.v1"
EXPECTED_ACCEPTANCE_SCHEMA = "missipy.route_pipeline.controlled_dev_post_execution_acceptance.v1"
DEFAULT_OUTPUT_NAME = "scheduler_integration_surface_audit.json"

SURFACE_SPECS = (
    {
        "path": "src/runtime/scheduler_route_adapter.py",
        "role": "scheduler_request_mapping_and_adapter",
        "required_symbols": ("scheduler_route_request_mapping",),
        "use_before_new_code": True,
    },
    {
        "path": "src/runtime/scheduler_route_handshake.py",
        "role": "scheduler_to_route_preparation_handshake",
        "required_symbols": ("prepare_route_for_scheduler",),
        "use_before_new_code": True,
    },
    {
        "path": "src/runtime/scheduler_route_handler_minimal.py",
        "role": "scheduler_command_to_routeproxy_frames",
        "required_symbols": (
            "build_single_frame_route_command",
            "handle_scheduler_route_command",
            "read_scheduler_route_handler_result_frames",
        ),
        "use_before_new_code": True,
    },
    {
        "path": "src/runtime/controlproxy_scheduler_handler.py",
        "role": "controlproxy_scheduler_wrapper_existing_surface",
        "required_symbols": ("handle_scheduler_route_request",),
        "use_before_new_code": True,
    },
    {
        "path": "src/runtime/route_proxy_runtime_minimal.py",
        "role": "routeproxy_runtime_policy_existing_surface",
        "required_symbols": ("RouteProxyRuntimePolicy", "prepare_route_proxy_runtime"),
        "use_before_new_code": True,
    },
    {
        "path": "src/runtime/shm_runtime_schema.py",
        "role": "event_context_bus_schema_existing_surface",
        "required_symbols": ("EventBusMessage", "ContextBusMessage"),
        "use_before_new_code": True,
    },
)

FALSE_EXECUTION_FLAGS = (
    "runtime_imports_executed_by_0200",
    "handler_called_by_0200",
    "routeproxy_prepared_by_0200",
    "read_route_frame_called_by_0200",
    "writer_permits_requested_by_0200",
    "frames_written_by_0200",
    "controlproxy_frames_written",
    "scheduler_modified",
    "eventbus_instantiated",
    "network_used",
)

FALSE_NEW_SURFACE_FLAGS = (
    "new_runtime_handler_added",
    "new_adapter_added",
    "new_bus_added",
    "new_sql_backend_added",
    "new_qdrant_backend_added",
    "new_github_client_added",
)


class SchedulerIntegrationSurfaceAuditError(ValueError):
    """Raised when the Scheduler integration surface audit input is unsafe."""


def audit_scheduler_integration_surfaces(
    *,
    acceptance_path: Path | str,
    repo_root: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Audit existing Scheduler integration surfaces without importing runtime modules."""

    root = Path(repo_root)
    acceptance_file = Path(acceptance_path)
    acceptance = _read_json_file(acceptance_file)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_acceptance(acceptance, issues, warnings)

    surface_reports = [
        _audit_surface(root=root, spec=spec)
        for spec in SURFACE_SPECS
    ]

    for report in surface_reports:
        if not report["exists"]:
            issues.append(f"missing existing surface: {report['path']}")
        for symbol in report["missing_required_symbols"]:
            issues.append(f"missing required symbol {symbol} in {report['path']}")

    recommended = _recommended_integration_path(surface_reports)
    if not recommended:
        issues.append("no recommended Scheduler integration path found from existing surfaces")

    if not root.exists():
        issues.append("repo_root must exist")
    if not root.is_dir():
        issues.append("repo_root must be a directory")

    target_runtime_root = Path(str(acceptance.get("target_runtime_root", "")))
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be scheduler_integration_surface_audit.json")

    audit = {
        "schema": SCHEDULER_INTEGRATION_SURFACE_AUDIT_SCHEMA,
        "bloc": "C",
        "bloc_name": "scheduler-hook-controlled",
        "acceptance_path": str(acceptance_file),
        "acceptance_schema": acceptance.get("schema"),
        "accepted_baseline": acceptance.get("accepted_baseline"),
        "controlled_dev_baseline_ref": acceptance.get("controlled_dev_baseline_ref"),
        "policy_decision_id": acceptance.get("policy_decision_id"),
        "target_runtime_root": acceptance.get("target_runtime_root"),
        "target_isolated_runtime_root": acceptance.get("target_isolated_runtime_root"),
        "repo_root": str(root),
        "surface_count": len(surface_reports),
        "existing_surface_count": sum(1 for item in surface_reports if item["exists"]),
        "surface_reports": surface_reports,
        "recommended_integration_path": recommended,
        "integration_surface_audit_success": not issues,
        "scheduler_hook_plan_allowed_next": not issues,
        "next_recommended_patch": "0202-scheduler_hook_dry_run_plan",
        "provenance_warning": _provenance_warning(acceptance),
        "issues": issues,
        "warnings": warnings + ([ _provenance_warning(acceptance) ] if _provenance_warning(acceptance) else []),
        "existing_surfaces_reused": True,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_scheduler_added": False,
        "new_routeproxy_runtime_added": False,
        "new_controlproxy_runtime_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "new_graph_renderer_added": False,
        "new_inference_path_added": False,
        "runtime_imports_executed_by_0201": False,
        "scheduler_run_executed": False,
        "handler_called_by_0201": False,
        "routeproxy_prepared_by_0201": False,
        "read_route_frame_called_by_0201": False,
        "writer_permits_requested_by_0201": False,
        "frames_written_by_0201": False,
        "controlproxy_frames_written_by_0201": False,
        "eventbus_instantiated_by_0201": False,
        "network_used_by_0201": False,
    }

    if output_path is not None:
        _write_audit(final_output, audit)

    return audit


def _audit_acceptance(acceptance: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if acceptance.get("schema") != EXPECTED_ACCEPTANCE_SCHEMA:
        issues.append("P0200 acceptance schema mismatch")
    if acceptance.get("controlled_dev_smoke_accepted") is not True:
        issues.append("controlled_dev_smoke_accepted must be true")
    if acceptance.get("bloc_b_complete") is not True:
        issues.append("bloc_b_complete must be true")
    if acceptance.get("next_bloc") != "C":
        issues.append("next_bloc must be C")
    if acceptance.get("issues") not in ([], None):
        issues.append("P0200 acceptance issues must be empty")
    if isinstance(acceptance.get("warnings"), list) and acceptance.get("warnings"):
        warnings.extend(str(item) for item in acceptance.get("warnings", []))
    if acceptance.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for flag in FALSE_EXECUTION_FLAGS:
        if acceptance.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if acceptance.get(flag) is not False:
            issues.append(f"{flag} must be false")
    if acceptance.get("frames_written_count") != 1:
        issues.append("frames_written_count must be 1")
    if acceptance.get("readback_count") != 1:
        issues.append("readback_count must be 1")
    if not isinstance(acceptance.get("policy_decision_id"), str) or not acceptance.get("policy_decision_id"):
        issues.append("policy_decision_id must be present")


def _audit_surface(*, root: Path, spec: Mapping[str, Any]) -> dict[str, Any]:
    relative = str(spec["path"])
    path = root / relative
    exists = path.exists()
    functions: list[str] = []
    classes: list[str] = []
    parse_error = ""
    text = ""
    if exists:
        text = path.read_text(encoding="utf-8")
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

    symbols = set(functions) | set(classes)
    required = tuple(spec.get("required_symbols", ()))
    missing = [symbol for symbol in required if symbol not in symbols and symbol not in text]
    matched = [symbol for symbol in required if symbol in symbols or symbol in text]
    return {
        "path": relative,
        "role": spec.get("role"),
        "exists": exists,
        "parse_error": parse_error,
        "function_count": len(functions),
        "class_count": len(classes),
        "functions": sorted(functions),
        "classes": sorted(classes),
        "required_symbols": list(required),
        "matched_required_symbols": matched,
        "missing_required_symbols": missing,
        "use_before_new_code": bool(spec.get("use_before_new_code")),
    }


def _recommended_integration_path(surface_reports: list[Mapping[str, Any]]) -> dict[str, Any]:
    by_role = {str(report.get("role")): report for report in surface_reports}
    command = by_role.get("scheduler_command_to_routeproxy_frames")
    adapter = by_role.get("scheduler_request_mapping_and_adapter")
    handshake = by_role.get("scheduler_to_route_preparation_handshake")
    if command and adapter and handshake:
        if not command.get("missing_required_symbols") and not adapter.get("missing_required_symbols"):
            return {
                "path": "adapter -> command builder -> minimal handler -> readback",
                "reuse_first": [
                    "src/runtime/scheduler_route_adapter.py",
                    "src/runtime/scheduler_route_handler_minimal.py",
                    "src/runtime/scheduler_route_handshake.py",
                ],
                "planner_patch": "0202-scheduler_hook_dry_run_plan",
                "execution_patch_later": "not before a dedicated controlled hook smoke patch",
            }
    return {}


def _provenance_warning(acceptance: Mapping[str, Any]) -> str:
    if not acceptance.get("source_baseline_ref") or not acceptance.get("source_entry_digest"):
        return "source_baseline_ref or source_entry_digest missing from P0200 acceptance; preserve this as a provenance repair item"
    return ""


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SchedulerIntegrationSurfaceAuditError("input must be a JSON object")
    return raw


def _write_audit(path: Path, audit: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise SchedulerIntegrationSurfaceAuditError("output filename must be scheduler_integration_surface_audit.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Scheduler integration surfaces.")
    parser.add_argument("--acceptance", required=True, help="Path to controlled_dev_routeproxy_smoke_post_execution_acceptance.json.")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect.")
    parser.add_argument("--output", help="Optional scheduler_integration_surface_audit.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    audit = audit_scheduler_integration_surfaces(
        acceptance_path=Path(args.acceptance),
        repo_root=Path(args.repo_root),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(f"integration_surface_audit_success: {audit['integration_surface_audit_success']}")
        print(f"scheduler_hook_plan_allowed_next: {audit['scheduler_hook_plan_allowed_next']}")
        print(f"existing_surface_count: {audit['existing_surface_count']}")
        print(f"next_recommended_patch: {audit['next_recommended_patch']}")
        print(f"issues: {len(audit['issues'])}")
        print(f"warnings: {len(audit['warnings'])}")
    return 0 if audit["integration_surface_audit_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
