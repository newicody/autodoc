#!/usr/bin/env python3
"""Plan ControlProxy stale priority zone smoke from the 0204 contract audit.

0205 is the Bloc D ControlProxy stale priority zone smoke plan only.

It reads controlproxy_contract_audit.json from 0204 and writes
controlproxy_stale_priority_zone_smoke_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0205 must reuse the 0204 ControlProxy contract audit before any stale priority
zone execution is allowed.

0205 must not introduce a new runtime handler, adapter, bus, Scheduler,
RouteProxy runtime, ControlProxy runtime, SQL backend, Qdrant backend, GitHub
client, graph renderer, or inference path.

0205 does not execute Scheduler.run.
0205 does not modify Scheduler.run.
0205 does not import runtime handler modules.
0205 does not call handle_scheduler_route_command.
0205 does not call handle_scheduler_route_request.
0205 does not call prepare_route_proxy_runtime.
0205 does not call mark_route_frame_stale.
0205 does not call read_route_frame.
0205 does not request writer permits.
0205 does not call write_route_frame.
0205 does not write ControlProxy or RouteProxy frames.
0205 does not call GitHub API or use network.

ControlProxy remains a coordination and contract surface, not business authority.
Scheduler/policy/zone remain authority.
RouteProxy remains the fast data-plane frame surface.
0205 plans stale priority zone behavior only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


CONTROLPROXY_STALE_PRIORITY_ZONE_SMOKE_PLAN_SCHEMA = (
    "missipy.controlproxy.stale_priority_zone_smoke_plan.v1"
)
EXPECTED_AUDIT_SCHEMA = "missipy.controlproxy.contract_audit.v1"
DEFAULT_OUTPUT_NAME = "controlproxy_stale_priority_zone_smoke_plan.json"

REQUIRED_CONTRACT_REUSE_PATHS = (
    "src/runtime/controlproxy_scheduler_handler.py",
    "src/runtime/scheduler_route_adapter.py",
    "src/runtime/scheduler_route_handler_minimal.py",
    "src/runtime/route_proxy_runtime_minimal.py",
)

OBSERVATION_REUSE_PATHS = (
    "src/runtime/shm_runtime_schema.py",
    "src/runtime/bus_visualization_adapter.py",
)

FALSE_AUDIT_FLAGS = (
    "runtime_imports_executed_by_0204",
    "scheduler_run_executed",
    "handler_called_by_0204",
    "routeproxy_prepared_by_0204",
    "read_route_frame_called_by_0204",
    "writer_permits_requested_by_0204",
    "frames_written_by_0204",
    "controlproxy_frames_written_by_0204",
    "eventbus_instantiated_by_0204",
    "network_used_by_0204",
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


class ControlProxyStalePriorityZoneSmokePlanError(ValueError):
    """Raised when the ControlProxy stale priority zone smoke plan is unsafe."""


def plan_controlproxy_stale_priority_zone_smoke(
    *,
    contract_audit_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build a stale priority zone smoke plan without executing runtime code."""

    audit_path = Path(contract_audit_path)
    audit = _read_json_file(audit_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_contract_audit(audit, issues, warnings)
    existing_surface_paths = _audit_surface_reports(audit, issues, warnings)

    target_runtime_root = Path(str(audit.get("target_runtime_root", "")))
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be controlproxy_stale_priority_zone_smoke_plan.json")

    provenance_repair_items = []
    if isinstance(audit.get("provenance_repair_items"), list):
        provenance_repair_items.extend(str(item) for item in audit.get("provenance_repair_items", []))

    plan = {
        "schema": CONTROLPROXY_STALE_PRIORITY_ZONE_SMOKE_PLAN_SCHEMA,
        "bloc": "D",
        "bloc_name": "controlproxy-contract-and-priority",
        "contract_audit_path": str(audit_path),
        "contract_audit_schema": audit.get("schema"),
        "accepted_baseline": audit.get("accepted_baseline"),
        "policy_decision_id": audit.get("policy_decision_id"),
        "target_runtime_root": audit.get("target_runtime_root"),
        "target_isolated_runtime_root": audit.get("target_isolated_runtime_root"),
        "recommended_contract": audit.get("recommended_contract"),
        "controlproxy_stale_priority_zone_smoke_plan_ready": not issues,
        "execution_allowed_by_0205": False,
        "controlproxy_frame_write_allowed_by_0205": False,
        "routeproxy_frame_write_allowed_by_0205": False,
        "p0206_may_execute_controlled_stale_priority_zone_smoke": not issues,
        "planned_next_patch": "0206-controlproxy_routeproxy_coherence_acceptance",
        "planned_contract_path": "Scheduler/policy/zone -> ControlProxy contract -> RouteProxy stale priority zone data-plane",
        "required_contract_reuse_paths": list(REQUIRED_CONTRACT_REUSE_PATHS),
        "observation_reuse_paths": list(OBSERVATION_REUSE_PATHS),
        "existing_surface_paths_from_audit": existing_surface_paths,
        "planned_smoke_steps": [
            {
                "step": "validate_authority_boundary",
                "authority": "Scheduler/policy/zone",
                "assertion": "ControlProxy is not business authority",
            },
            {
                "step": "select_policy_scoped_route",
                "surface": "src/runtime/scheduler_route_adapter.py",
                "assertion": "policy_decision_id and zone scope must be explicit",
            },
            {
                "step": "plan_priority_update",
                "surface": "src/runtime/scheduler_route_handler_minimal.py",
                "assertion": "priority remains policy-scoped metadata",
            },
            {
                "step": "plan_stale_mark",
                "surface": "src/runtime/route_proxy_runtime_minimal.py",
                "symbol": "mark_route_frame_stale",
                "assertion": "stale mark must stay under target_isolated_runtime_root",
            },
            {
                "step": "plan_readback",
                "surface": "src/runtime/route_proxy_runtime_minimal.py",
                "symbol": "read_route_frame",
                "assertion": "readback proves stale/priority/zone coherence",
            },
            {
                "step": "record_observation_only",
                "surface": "src/runtime/shm_runtime_schema.py",
                "assertion": "EventBus/ContextBus records observations only, not commands",
            },
        ],
        "dry_run_boundaries": [
            "P0205 does not execute Scheduler.run",
            "P0205 does not modify Scheduler.run",
            "P0205 does not write ControlProxy frames",
            "P0205 does not write RouteProxy frames",
            "P0205 does not call mark_route_frame_stale",
            "P0205 does not request writer permits",
            "P0205 does not create a new ControlProxy runtime",
        ],
        "p0206_execution_unlock_requirements": [
            "explicit controlled stale priority zone smoke patch",
            "explicit policy_decision_id",
            "reuse existing ControlProxy and RouteProxy contract surfaces",
            "ControlProxy remains not business authority",
            "Scheduler/policy/zone remain authority",
            "RouteProxy writes restricted to target_isolated_runtime_root",
            "ControlProxy frames remain false unless P0206 explicitly audits and permits a contract observation",
            "Scheduler.run modification remains false",
            "post-smoke acceptance closes Bloc D",
        ],
        "contract_decisions": list(audit.get("contract_decisions", []))
        if isinstance(audit.get("contract_decisions"), list)
        else [],
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
        "runtime_imports_executed_by_0205": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0205": False,
        "routeproxy_prepared_by_0205": False,
        "mark_route_frame_stale_called_by_0205": False,
        "read_route_frame_called_by_0205": False,
        "writer_permits_requested_by_0205": False,
        "frames_written_by_0205": False,
        "controlproxy_frames_written_by_0205": False,
        "eventbus_instantiated_by_0205": False,
        "network_used_by_0205": False,
    }

    if output_path is not None:
        _write_plan(final_output, plan)

    return plan


def _audit_contract_audit(audit: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if audit.get("schema") != EXPECTED_AUDIT_SCHEMA:
        issues.append("controlproxy contract audit schema mismatch")
    if audit.get("controlproxy_contract_audit_success") is not True:
        issues.append("controlproxy_contract_audit_success must be true")
    if audit.get("stale_priority_zone_plan_allowed_next") is not True:
        issues.append("stale_priority_zone_plan_allowed_next must be true")
    if audit.get("next_recommended_patch") != "0205-controlproxy_stale_priority_zone_smoke_plan":
        issues.append("next_recommended_patch must be 0205-controlproxy_stale_priority_zone_smoke_plan")
    if audit.get("issues") not in ([], None):
        issues.append("controlproxy contract audit issues must be empty")
    if isinstance(audit.get("warnings"), list) and audit.get("warnings"):
        warnings.extend(str(item) for item in audit.get("warnings", []))
    if audit.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    recommended = audit.get("recommended_contract")
    if not isinstance(recommended, Mapping):
        issues.append("recommended_contract must be present")
    else:
        if recommended.get("authority") != "Scheduler/policy/zone":
            issues.append("recommended_contract authority must be Scheduler/policy/zone")
        if recommended.get("coordination_surface") != "ControlProxy":
            issues.append("recommended_contract coordination_surface must be ControlProxy")
        if recommended.get("data_plane") != "RouteProxy":
            issues.append("recommended_contract data_plane must be RouteProxy")
    for flag in FALSE_AUDIT_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _audit_surface_reports(
    audit: Mapping[str, Any],
    issues: list[str],
    warnings: list[str],
) -> list[str]:
    reports = audit.get("surface_reports")
    if not isinstance(reports, list):
        issues.append("surface_reports must be a list")
        return []
    by_path: dict[str, Mapping[str, Any]] = {}
    for report in reports:
        if isinstance(report, Mapping) and isinstance(report.get("path"), str):
            by_path[str(report["path"])] = report

    for path in REQUIRED_CONTRACT_REUSE_PATHS:
        report = by_path.get(path)
        if not report:
            issues.append(f"missing required contract surface report: {path}")
            continue
        if report.get("exists") is not True:
            issues.append(f"required contract surface missing: {path}")
        if report.get("missing_required_symbols") not in ([], None):
            issues.append(f"required contract surface missing symbols: {path}")
        if report.get("missing_required_tokens") not in ([], None):
            issues.append(f"required contract surface missing tokens: {path}")
        if report.get("use_before_new_code") is not True:
            issues.append(f"required contract surface must be marked use_before_new_code: {path}")

    for path in OBSERVATION_REUSE_PATHS:
        report = by_path.get(path)
        if not report:
            warnings.append(f"observation surface report missing: {path}")
            continue
        if report.get("exists") is not True:
            warnings.append(f"observation surface missing: {path}")
        if report.get("missing_required_symbols") not in ([], None):
            warnings.append(f"observation surface missing symbols: {path}")
        if report.get("missing_required_tokens") not in ([], None):
            warnings.append(f"observation surface missing tokens: {path}")

    return sorted(by_path)


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ControlProxyStalePriorityZoneSmokePlanError("input must be a JSON object")
    return raw


def _write_plan(path: Path, plan: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ControlProxyStalePriorityZoneSmokePlanError(
            "output filename must be controlproxy_stale_priority_zone_smoke_plan.json"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan ControlProxy stale priority zone smoke.")
    parser.add_argument("--contract-audit", required=True, help="Path to controlproxy_contract_audit.json.")
    parser.add_argument("--output", help="Optional controlproxy_stale_priority_zone_smoke_plan.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    plan = plan_controlproxy_stale_priority_zone_smoke(
        contract_audit_path=Path(args.contract_audit),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"controlproxy_stale_priority_zone_smoke_plan_ready: {plan['controlproxy_stale_priority_zone_smoke_plan_ready']}")
        print(f"execution_allowed_by_0205: {plan['execution_allowed_by_0205']}")
        print(f"p0206_may_execute_controlled_stale_priority_zone_smoke: {plan['p0206_may_execute_controlled_stale_priority_zone_smoke']}")
        print(f"planned_next_patch: {plan['planned_next_patch']}")
        print(f"issues: {len(plan['issues'])}")
        print(f"warnings: {len(plan['warnings'])}")
    return 0 if plan["controlproxy_stale_priority_zone_smoke_plan_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
