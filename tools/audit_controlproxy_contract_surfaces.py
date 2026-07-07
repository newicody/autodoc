#!/usr/bin/env python3
"""Audit existing ControlProxy contract surfaces after Bloc C.

0204 is the Bloc D ControlProxy contract audit only.

It reads controlled_scheduler_hook_smoke_acceptance.json from 0203, inspects
existing source files by AST/text, and writes controlproxy_contract_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0204 must audit existing ControlProxy and RouteProxy contract surfaces before
any stale/priority/zone smoke plan is allowed.

0204 must not introduce a new runtime handler, adapter, bus, Scheduler,
RouteProxy runtime, ControlProxy runtime, SQL backend, Qdrant backend, GitHub
client, graph renderer, or inference path.

0204 does not execute Scheduler.run.
0204 does not import runtime handler modules.
0204 does not call handle_scheduler_route_command.
0204 does not call handle_scheduler_route_request.
0204 does not call prepare_route_proxy_runtime.
0204 does not call read_route_frame.
0204 does not request writer permits.
0204 does not call write_route_frame.
0204 does not write ControlProxy or RouteProxy frames.
0204 does not call GitHub API or use network.

ControlProxy remains a contract and coordination surface, not business authority.
Scheduler/policy/zone remain authority.
RouteProxy remains the fast data-plane frame surface.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Mapping


CONTROLPROXY_CONTRACT_AUDIT_SCHEMA = "missipy.controlproxy.contract_audit.v1"
EXPECTED_ACCEPTANCE_SCHEMA = "missipy.scheduler.controlled_hook_smoke_acceptance.v1"
DEFAULT_OUTPUT_NAME = "controlproxy_contract_audit.json"

SURFACE_SPECS = (
    {
        "path": "src/runtime/controlproxy_scheduler_handler.py",
        "role": "controlproxy_scheduler_existing_wrapper",
        "required_symbols": (
            "ControlProxySchedulerRouteRequestHandler",
            "handle_scheduler_route_request",
            "resolve_scheduler_route_request_handler",
            "scheduler_route_request_payload",
        ),
        "required_tokens": ("ControlProxy", "SchedulerRouteRequest", "handle"),
    },
    {
        "path": "src/runtime/scheduler_route_adapter.py",
        "role": "scheduler_policy_request_adapter",
        "required_symbols": (
            "SchedulerRouteRequest",
            "SchedulerRouteReply",
            "scheduler_route_request_mapping",
            "handle_scheduler_route_request",
        ),
        "required_tokens": ("policy_decision_id", "scope", "holder"),
    },
    {
        "path": "src/runtime/scheduler_route_handler_minimal.py",
        "role": "scheduler_command_to_routeproxy_contract",
        "required_symbols": (
            "SchedulerRouteHandlerCommand",
            "build_single_frame_route_command",
            "handle_scheduler_route_command",
            "read_scheduler_route_handler_result_frames",
        ),
        "required_tokens": ("priority", "runtime_policy", "route_ref"),
    },
    {
        "path": "src/runtime/route_proxy_runtime_minimal.py",
        "role": "routeproxy_data_plane_stale_priority_zone_contract",
        "required_symbols": (
            "RouteProxyRuntimePolicy",
            "prepare_route_proxy_runtime",
            "request_writer_permit",
            "write_route_frame",
            "read_route_frame",
            "mark_route_frame_stale",
        ),
        "required_tokens": ("stale", "priority", "route_root"),
    },
    {
        "path": "src/runtime/shm_runtime_schema.py",
        "role": "event_context_observation_schema",
        "required_symbols": ("EventBusMessage", "ContextBusMessage", "RouteMessage"),
        "required_tokens": ("topic", "schema", "payload"),
    },
    {
        "path": "src/runtime/bus_visualization_adapter.py",
        "role": "representation_only_graph_surface",
        "required_symbols": (),
        "required_tokens": ("graph", "edge", "node"),
        "optional": True,
    },
)

FALSE_ACCEPTANCE_FLAGS = (
    "scheduler_run_executed",
    "scheduler_run_modified",
    "controlproxy_frames_written",
    "scheduler_modified",
    "eventbus_instantiated",
    "network_used",
)

FALSE_NEW_SURFACE_FLAGS = (
    "new_runtime_handler_added",
    "new_adapter_added",
    "new_bus_added",
    "new_scheduler_added",
    "new_routeproxy_runtime_added",
    "new_controlproxy_runtime_added",
    "new_sql_backend_added",
    "new_qdrant_backend_added",
    "new_github_client_added",
    "new_graph_renderer_added",
    "new_inference_path_added",
)


class ControlProxyContractAuditError(ValueError):
    """Raised when ControlProxy contract audit input is unsafe."""


def audit_controlproxy_contract_surfaces(
    *,
    acceptance_path: Path | str,
    repo_root: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Audit existing ControlProxy/RouteProxy contract surfaces without imports."""

    acceptance_file = Path(acceptance_path)
    root = Path(repo_root)
    acceptance = _read_json_file(acceptance_file)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_acceptance(acceptance, issues, warnings)

    surface_reports = [_audit_surface(root=root, spec=spec) for spec in SURFACE_SPECS]
    for report in surface_reports:
        if report["optional"]:
            if not report["exists"]:
                warnings.append(f"optional representation surface missing: {report['path']}")
                continue
            for symbol in report["missing_required_symbols"]:
                warnings.append(f"optional representation surface missing symbol {symbol} in {report['path']}")
            for token in report["missing_required_tokens"]:
                warnings.append(f"optional representation surface missing token {token} in {report['path']}")
            continue
        if not report["exists"]:
            issues.append(f"missing existing surface: {report['path']}")
        for symbol in report["missing_required_symbols"]:
            issues.append(f"missing required symbol {symbol} in {report['path']}")
        for token in report["missing_required_tokens"]:
            issues.append(f"missing required token {token} in {report['path']}")

    recommended_contract = _recommended_contract(surface_reports)
    if not recommended_contract:
        issues.append("no recommended ControlProxy contract path found from existing surfaces")

    if not root.exists():
        issues.append("repo_root must exist")
    if not root.is_dir():
        issues.append("repo_root must be a directory")

    target_runtime_root = Path(str(acceptance.get("target_runtime_root", "")))
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be controlproxy_contract_audit.json")

    provenance_repair_items = []
    if isinstance(acceptance.get("provenance_repair_items"), list):
        provenance_repair_items.extend(str(item) for item in acceptance.get("provenance_repair_items", []))

    audit = {
        "schema": CONTROLPROXY_CONTRACT_AUDIT_SCHEMA,
        "bloc": "D",
        "bloc_name": "controlproxy-contract-and-priority",
        "acceptance_path": str(acceptance_file),
        "acceptance_schema": acceptance.get("schema"),
        "accepted_baseline": acceptance.get("accepted_baseline"),
        "policy_decision_id": acceptance.get("policy_decision_id"),
        "target_runtime_root": acceptance.get("target_runtime_root"),
        "target_isolated_runtime_root": acceptance.get("target_isolated_runtime_root"),
        "repo_root": str(root),
        "surface_count": len(surface_reports),
        "existing_surface_count": sum(1 for item in surface_reports if item["exists"]),
        "surface_reports": surface_reports,
        "recommended_contract": recommended_contract,
        "controlproxy_contract_audit_success": not issues,
        "stale_priority_zone_plan_allowed_next": not issues,
        "next_recommended_patch": "0205-controlproxy_stale_priority_zone_smoke_plan",
        "contract_decisions": [
            "ControlProxy remains a coordination and contract surface, not business authority.",
            "Scheduler/policy/zone remain authority.",
            "RouteProxy remains the fast data-plane frame surface.",
            "stale, priority, and zone behavior must be policy-scoped and auditable.",
            "Any future ControlProxy frame write requires explicit phase unlock and acceptance.",
        ],
        "provenance_repair_items": provenance_repair_items,
        "issues": issues,
        "warnings": warnings,
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
        "runtime_imports_executed_by_0204": False,
        "scheduler_run_executed": False,
        "handler_called_by_0204": False,
        "routeproxy_prepared_by_0204": False,
        "read_route_frame_called_by_0204": False,
        "writer_permits_requested_by_0204": False,
        "frames_written_by_0204": False,
        "controlproxy_frames_written_by_0204": False,
        "eventbus_instantiated_by_0204": False,
        "network_used_by_0204": False,
    }

    if output_path is not None:
        _write_audit(final_output, audit)

    return audit


def _audit_acceptance(acceptance: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if acceptance.get("schema") != EXPECTED_ACCEPTANCE_SCHEMA:
        issues.append("P0203 acceptance schema mismatch")
    if acceptance.get("controlled_scheduler_hook_smoke_accepted") is not True:
        issues.append("controlled_scheduler_hook_smoke_accepted must be true")
    if acceptance.get("bloc_c_complete") is not True:
        issues.append("bloc_c_complete must be true")
    if acceptance.get("next_bloc") != "D":
        issues.append("next_bloc must be D")
    if acceptance.get("issues") not in ([], None):
        issues.append("P0203 acceptance issues must be empty")
    if isinstance(acceptance.get("warnings"), list) and acceptance.get("warnings"):
        warnings.extend(str(item) for item in acceptance.get("warnings", []))
    if acceptance.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for flag in FALSE_ACCEPTANCE_FLAGS:
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
    optional = bool(spec.get("optional"))
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
    required_symbols = tuple(spec.get("required_symbols", ()))
    required_tokens = tuple(spec.get("required_tokens", ()))
    missing_symbols = [symbol for symbol in required_symbols if symbol not in symbols and symbol not in text]
    missing_tokens = [token for token in required_tokens if token not in text]
    return {
        "path": relative,
        "role": spec.get("role"),
        "optional": optional,
        "exists": exists,
        "parse_error": parse_error,
        "function_count": len(functions),
        "class_count": len(classes),
        "functions": sorted(functions),
        "classes": sorted(classes),
        "required_symbols": list(required_symbols),
        "required_tokens": list(required_tokens),
        "matched_required_symbols": [
            symbol for symbol in required_symbols if symbol in symbols or symbol in text
        ],
        "missing_required_symbols": missing_symbols,
        "missing_required_tokens": missing_tokens,
        "use_before_new_code": True,
    }


def _recommended_contract(surface_reports: list[Mapping[str, Any]]) -> dict[str, Any]:
    by_path = {str(report.get("path")): report for report in surface_reports}
    required = (
        "src/runtime/controlproxy_scheduler_handler.py",
        "src/runtime/scheduler_route_adapter.py",
        "src/runtime/scheduler_route_handler_minimal.py",
        "src/runtime/route_proxy_runtime_minimal.py",
    )
    for path in required:
        report = by_path.get(path)
        if not report or report.get("exists") is not True:
            return {}
        if report.get("missing_required_symbols") or report.get("missing_required_tokens"):
            return {}
    return {
        "path": "scheduler authority -> ControlProxy contract wrapper -> RouteProxy data-plane",
        "authority": "Scheduler/policy/zone",
        "coordination_surface": "ControlProxy",
        "data_plane": "RouteProxy",
        "planned_next_patch": "0205-controlproxy_stale_priority_zone_smoke_plan",
        "reuse_first": list(required),
        "forbidden_until_explicit_unlock": [
            "ControlProxy frame writes",
            "Scheduler.run modification",
            "production route writes",
            "new ControlProxy runtime",
            "new RouteProxy runtime",
        ],
    }


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ControlProxyContractAuditError("input must be a JSON object")
    return raw


def _write_audit(path: Path, audit: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ControlProxyContractAuditError("output filename must be controlproxy_contract_audit.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit ControlProxy contract surfaces.")
    parser.add_argument("--acceptance", required=True, help="Path to controlled_scheduler_hook_smoke_acceptance.json.")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect.")
    parser.add_argument("--output", help="Optional controlproxy_contract_audit.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    audit = audit_controlproxy_contract_surfaces(
        acceptance_path=Path(args.acceptance),
        repo_root=Path(args.repo_root),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(f"controlproxy_contract_audit_success: {audit['controlproxy_contract_audit_success']}")
        print(f"stale_priority_zone_plan_allowed_next: {audit['stale_priority_zone_plan_allowed_next']}")
        print(f"existing_surface_count: {audit['existing_surface_count']}")
        print(f"next_recommended_patch: {audit['next_recommended_patch']}")
        print(f"issues: {len(audit['issues'])}")
        print(f"warnings: {len(audit['warnings'])}")
    return 0 if audit["controlproxy_contract_audit_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
