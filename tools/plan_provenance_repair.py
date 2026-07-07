#!/usr/bin/env python3
"""Plan forward-only provenance repair from the 0207 audit.

0208 is the Bloc E provenance repair plan only.

It reads provenance_repair_audit.json from 0207 and writes
provenance_repair_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0208 must plan a forward-only provenance repair before any provenance repair
acceptance write is allowed.

0208 does not repair source_baseline_ref.
0208 does not repair source_entry_digest.
0208 does not rewrite controlled_dev_routeproxy_smoke_post_execution_acceptance.json.
0208 does not rewrite runtime history.
0208 does not write SQL.
0208 does not write Qdrant.
0208 does not execute Scheduler.run.
0208 does not modify Scheduler.run.
0208 does not import runtime handler modules.
0208 does not call handle_scheduler_route_command.
0208 does not call handle_scheduler_route_request.
0208 does not call prepare_route_proxy_runtime.
0208 does not call mark_route_frame_stale.
0208 does not call read_route_frame.
0208 does not request writer permits.
0208 does not call write_route_frame.
0208 does not write ControlProxy or RouteProxy frames.
0208 does not call GitHub API or use network.

0208 selects source_baseline_ref and source_entry_digest candidates but writes
only a plan. The repair itself is deferred to P0209.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


PROVENANCE_REPAIR_PLAN_SCHEMA = "missipy.provenance.repair_plan.v1"
EXPECTED_AUDIT_SCHEMA = "missipy.provenance.repair_audit.v1"
DEFAULT_OUTPUT_NAME = "provenance_repair_plan.json"
TARGET_SOURCE_ARTIFACT = "controlled_dev_routeproxy_smoke_post_execution_acceptance.json"
REGISTRY_ARTIFACT = "controlled_dev_routeproxy_smoke_registry.jsonl"

FALSE_AUDIT_FLAGS = (
    "execution_allowed_by_0207",
    "sql_write_allowed_by_0207",
    "qdrant_write_allowed_by_0207",
    "runtime_history_rewrite_allowed_by_0207",
    "runtime_imports_executed_by_0207",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0207",
    "routeproxy_prepared_by_0207",
    "mark_route_frame_stale_called_by_0207",
    "read_route_frame_called_by_0207",
    "writer_permits_requested_by_0207",
    "frames_written_by_0207",
    "controlproxy_frames_written_by_0207",
    "eventbus_instantiated_by_0207",
    "network_used_by_0207",
    "sql_written_by_0207",
    "qdrant_written_by_0207",
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


class ProvenanceRepairPlanError(ValueError):
    """Raised when provenance repair planning is unsafe."""


def plan_forward_only_provenance_repair(
    *,
    provenance_repair_audit_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Plan forward-only provenance repair without writing repaired provenance."""

    audit_path = Path(provenance_repair_audit_path)
    audit = _read_json_file(audit_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_repair_audit(audit, issues, warnings)

    target_runtime_root = Path(str(audit.get("target_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be provenance_repair_plan.json")

    candidates = audit.get("candidate_provenance_refs")
    if not isinstance(candidates, list):
        candidates = []
        issues.append("candidate_provenance_refs must be a list")

    planned_source_baseline_ref = _select_candidate(
        candidates,
        artifact=TARGET_SOURCE_ARTIFACT,
        field="controlled_dev_baseline_ref",
    )
    planned_source_entry_digest = _select_candidate(
        candidates,
        artifact=REGISTRY_ARTIFACT,
        field="entry_digest",
    )
    registry_entry_ref = _select_candidate(candidates, artifact=REGISTRY_ARTIFACT, field="entry_ref")

    if not planned_source_baseline_ref:
        issues.append("missing planned source_baseline_ref candidate")
    if not planned_source_entry_digest:
        issues.append("missing planned source_entry_digest candidate")

    repair_items = list(audit.get("repair_items", [])) if isinstance(audit.get("repair_items"), list) else []
    if not repair_items:
        issues.append("repair_items must be present")

    plan = {
        "schema": PROVENANCE_REPAIR_PLAN_SCHEMA,
        "bloc": "E",
        "bloc_name": "sql-qdrant-provenance-repair",
        "provenance_repair_audit_path": str(audit_path),
        "provenance_repair_audit_schema": audit.get("schema"),
        "target_runtime_root": audit.get("target_runtime_root"),
        "target_isolated_runtime_root": audit.get("target_isolated_runtime_root"),
        "source_artifact": TARGET_SOURCE_ARTIFACT,
        "registry_artifact": REGISTRY_ARTIFACT,
        "missing_fields": [
            "source_baseline_ref",
            "source_entry_digest",
        ],
        "repair_strategy": "forward_only_artifact",
        "planned_output": "provenance_repair_acceptance.json",
        "planned_next_patch": "0209-forward_only_provenance_repair_acceptance",
        "provenance_repair_plan_ready": not issues,
        "provenance_repair_required": bool(audit.get("provenance_repair_required")),
        "source_baseline_ref_missing": bool(audit.get("source_baseline_ref_missing")),
        "source_entry_digest_missing": bool(audit.get("source_entry_digest_missing")),
        "planned_source_baseline_ref": planned_source_baseline_ref,
        "planned_source_baseline_ref_source": {
            "artifact": TARGET_SOURCE_ARTIFACT,
            "field": "controlled_dev_baseline_ref",
        },
        "planned_source_entry_digest": planned_source_entry_digest,
        "planned_source_entry_digest_source": {
            "artifact": REGISTRY_ARTIFACT,
            "field": "entry_digest",
        },
        "planned_registry_entry_ref": registry_entry_ref,
        "repair_items": repair_items,
        "candidate_provenance_refs": candidates,
        "repair_output_mode": "append-only forward artifact",
        "runtime_history_rewrite_allowed_by_0208": False,
        "execution_allowed_by_0208": False,
        "sql_write_allowed_by_0208": False,
        "qdrant_write_allowed_by_0208": False,
        "provenance_repair_write_allowed_by_0208": False,
        "p0209_may_write_forward_only_provenance_repair": not issues,
        "p0209_execution_unlock_requirements": [
            "explicit forward-only provenance repair acceptance patch",
            "write provenance_repair_acceptance.json only",
            "do not rewrite historical runtime artifacts",
            "do not write SQL directly",
            "do not write Qdrant directly",
            "include source_baseline_ref proof",
            "include source_entry_digest proof",
            "close Bloc E only after acceptance",
        ],
        "repair_boundaries": [
            "P0208 does not repair source_baseline_ref.",
            "P0208 does not repair source_entry_digest.",
            "P0208 does not rewrite runtime history.",
            "P0208 does not write SQL.",
            "P0208 does not write Qdrant.",
            "P0208 only plans a forward-only provenance repair.",
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
        "runtime_imports_executed_by_0208": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0208": False,
        "routeproxy_prepared_by_0208": False,
        "mark_route_frame_stale_called_by_0208": False,
        "read_route_frame_called_by_0208": False,
        "writer_permits_requested_by_0208": False,
        "frames_written_by_0208": False,
        "controlproxy_frames_written_by_0208": False,
        "eventbus_instantiated_by_0208": False,
        "network_used_by_0208": False,
        "sql_written_by_0208": False,
        "qdrant_written_by_0208": False,
    }

    if output_path is not None:
        _write_plan(final_output, plan)

    return plan


def _audit_repair_audit(audit: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if audit.get("schema") != EXPECTED_AUDIT_SCHEMA:
        issues.append("provenance repair audit schema mismatch")
    if audit.get("provenance_repair_audit_success") is not True:
        issues.append("provenance_repair_audit_success must be true")
    if audit.get("provenance_repair_required") is not True:
        issues.append("provenance_repair_required must be true")
    if audit.get("source_baseline_ref_missing") is not True:
        issues.append("source_baseline_ref_missing must be true")
    if audit.get("source_entry_digest_missing") is not True:
        issues.append("source_entry_digest_missing must be true")
    if audit.get("provenance_repair_plan_allowed_next") is not True:
        issues.append("provenance_repair_plan_allowed_next must be true")
    if audit.get("planned_next_patch") != "0208-provenance_repair_plan":
        issues.append("planned_next_patch must be 0208-provenance_repair_plan")
    if audit.get("issues") not in ([], None):
        issues.append("provenance repair audit issues must be empty")
    if isinstance(audit.get("warnings"), list) and audit.get("warnings"):
        warnings.extend(str(item) for item in audit.get("warnings", []))
    for flag in FALSE_AUDIT_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _select_candidate(candidates: list[Any], *, artifact: str, field: str) -> str:
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        if candidate.get("artifact") == artifact and candidate.get("field") == field:
            value = candidate.get("value")
            if isinstance(value, str) and value:
                return value
    return ""


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ProvenanceRepairPlanError("input must be a JSON object")
    return raw


def _write_plan(path: Path, plan: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ProvenanceRepairPlanError("output filename must be provenance_repair_plan.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan forward-only provenance repair.")
    parser.add_argument("--provenance-repair-audit", required=True, help="Path to provenance_repair_audit.json.")
    parser.add_argument("--output", help="Optional provenance_repair_plan.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    plan = plan_forward_only_provenance_repair(
        provenance_repair_audit_path=Path(args.provenance_repair_audit),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"provenance_repair_plan_ready: {plan['provenance_repair_plan_ready']}")
        print(f"planned_source_baseline_ref: {plan['planned_source_baseline_ref']}")
        print(f"planned_source_entry_digest: {plan['planned_source_entry_digest']}")
        print(f"p0209_may_write_forward_only_provenance_repair: {plan['p0209_may_write_forward_only_provenance_repair']}")
        print(f"planned_next_patch: {plan['planned_next_patch']}")
        print(f"issues: {len(plan['issues'])}")
        print(f"warnings: {len(plan['warnings'])}")
    return 0 if plan["provenance_repair_plan_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
