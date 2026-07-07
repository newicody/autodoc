#!/usr/bin/env python3
"""Accept promotion readiness for the isolated route pipeline.

0196 is a promotion readiness acceptance gate only.

It reads isolated_route_pipeline_promotion_plan_audit.json from 0195 and writes
isolated_route_pipeline_promotion_readiness_acceptance.json. It accepts that the
controlled-dev-routeproxy-smoke plan is ready for a later patch to execute, but
it does not allow execution itself.

It must reuse the existing 0195 promotion plan audit artifact. It must not
introduce a new runtime handler, adapter, bus, RouteProxy runtime, ControlProxy
runtime, SQL backend, Qdrant backend, GitHub client, graph renderer, or
inference path.

It does not execute controlled-dev-routeproxy-smoke.
It does not import runtime handler modules.
It does not call handle_scheduler_route_command.
It does not call handle_scheduler_route_request.
It does not call prepare_route_proxy_runtime.
It does not call read_route_frame.
It does not request writer permits.
It does not call write_route_frame.
It does not modify Scheduler.run.
It does not instantiate Scheduler.
It does not instantiate EventBus.
It does not write ControlProxy or RouteProxy frames.
It does not call GitHub API or use network.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


ISOLATED_ROUTE_PIPELINE_PROMOTION_READINESS_ACCEPTANCE_SCHEMA = (
    "missipy.route_pipeline.isolated_promotion_readiness_acceptance.v1"
)
EXPECTED_AUDIT_SCHEMA = "missipy.route_pipeline.isolated_promotion_plan_audit.v1"
EXPECTED_BASELINE = "isolated-route-pipeline-write-read-v1"
EXPECTED_PROMOTION_TARGET = "controlled-dev-routeproxy-smoke"
DEFAULT_OUTPUT_NAME = "isolated_route_pipeline_promotion_readiness_acceptance.json"

FALSE_SAFETY_FLAGS = (
    "runtime_imports_executed",
    "handler_called",
    "routeproxy_prepared",
    "read_route_frame_called",
    "writer_permits_requested",
    "frames_written",
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


class IsolatedRoutePipelinePromotionReadinessAcceptanceError(ValueError):
    """Raised when a readiness acceptance input is unsafe."""


def accept_isolated_route_pipeline_promotion_readiness(
    *,
    promotion_plan_audit_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Accept a clean 0195 promotion plan audit without executing the plan."""

    path = Path(promotion_plan_audit_path)
    audit = _read_json_file(path)
    issues: list[str] = []
    warnings: list[str] = []

    if audit.get("schema") != EXPECTED_AUDIT_SCHEMA:
        issues.append("promotion plan audit schema mismatch")
    if audit.get("audit_success") is not True:
        issues.append("audit_success must be true")
    if audit.get("issues") not in ([], None):
        issues.append("audit issues must be empty")
    if isinstance(audit.get("warnings"), list) and audit.get("warnings"):
        warnings.extend(str(item) for item in audit.get("warnings", []))
    if audit.get("accepted_baseline") != EXPECTED_BASELINE:
        issues.append("accepted_baseline mismatch")
    if audit.get("promotion_target") != EXPECTED_PROMOTION_TARGET:
        issues.append("promotion_target mismatch")
    if audit.get("promotion_ready") is not True:
        issues.append("promotion_ready must be true")
    if audit.get("promotion_allowed_by_0194") is not False:
        issues.append("promotion_allowed_by_0194 must remain false")
    if audit.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    if not isinstance(audit.get("selected_baseline_ref"), str) or not audit.get("selected_baseline_ref"):
        issues.append("selected_baseline_ref must be present")
    if not isinstance(audit.get("selected_entry_digest"), str) or not audit.get("selected_entry_digest"):
        issues.append("selected_entry_digest must be present")

    _audit_target_roots(audit, issues)
    _audit_counts(audit, issues)
    _audit_false_flags(audit, FALSE_SAFETY_FLAGS, issues)
    _audit_false_flags(audit, FALSE_NEW_SURFACE_FLAGS, issues)

    acceptance = {
        "schema": ISOLATED_ROUTE_PIPELINE_PROMOTION_READINESS_ACCEPTANCE_SCHEMA,
        "promotion_plan_audit_path": str(path),
        "promotion_plan_audit_schema": audit.get("schema"),
        "selected_baseline_ref": audit.get("selected_baseline_ref"),
        "selected_entry_digest": audit.get("selected_entry_digest"),
        "accepted_baseline": audit.get("accepted_baseline"),
        "source_policy_decision_id": audit.get("source_policy_decision_id"),
        "source_runtime_root": audit.get("source_runtime_root"),
        "source_isolated_runtime_root": audit.get("source_isolated_runtime_root"),
        "target_runtime_root": audit.get("target_runtime_root"),
        "target_isolated_runtime_root": audit.get("target_isolated_runtime_root"),
        "promotion_target": audit.get("promotion_target"),
        "promotion_readiness_accepted": not issues,
        "controlled_dev_smoke_ready": not issues,
        "execution_allowed_by_0196": False,
        "next_required_patch": "0197-bloc_a_coherence_record",
        "issues": issues,
        "warnings": warnings,
        "existing_surfaces_reused": True,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "runtime_imports_executed": False,
        "handler_called": False,
        "routeproxy_prepared": False,
        "read_route_frame_called": False,
        "writer_permits_requested": False,
        "frames_written": False,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "eventbus_instantiated": False,
        "network_used": False,
        "phase_re_evaluation_required_before_execution": True,
    }

    if output_path is not None:
        _write_acceptance(Path(output_path), acceptance)

    return acceptance


def _audit_target_roots(audit: Mapping[str, Any], issues: list[str]) -> None:
    target_runtime_root = audit.get("target_runtime_root")
    target_isolated_runtime_root = audit.get("target_isolated_runtime_root")
    if not isinstance(target_runtime_root, str) or not target_runtime_root:
        issues.append("target_runtime_root must be present")
        return
    if not isinstance(target_isolated_runtime_root, str) or not target_isolated_runtime_root:
        issues.append("target_isolated_runtime_root must be present")
        return

    runtime = Path(target_runtime_root)
    isolated = Path(target_isolated_runtime_root)
    if not runtime.is_absolute():
        issues.append("target_runtime_root must be absolute")
    if not isolated.is_absolute():
        issues.append("target_isolated_runtime_root must be absolute")
    if runtime == isolated:
        issues.append("target_runtime_root and target_isolated_runtime_root must be distinct")
    if runtime.is_absolute() and isolated.is_absolute() and not _is_within_or_equal(isolated, runtime):
        issues.append("target_isolated_runtime_root must be inside target_runtime_root")


def _audit_counts(audit: Mapping[str, Any], issues: list[str]) -> None:
    planned_step_count = audit.get("planned_step_count")
    required_precondition_count = audit.get("required_precondition_count")
    if not isinstance(planned_step_count, int) or planned_step_count < 4:
        issues.append("planned_step_count must be at least 4")
    if not isinstance(required_precondition_count, int) or required_precondition_count < 7:
        issues.append("required_precondition_count must be at least 7")


def _audit_false_flags(audit: Mapping[str, Any], flags: tuple[str, ...], issues: list[str]) -> None:
    for flag in flags:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _is_within_or_equal(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise IsolatedRoutePipelinePromotionReadinessAcceptanceError("promotion plan audit must be a JSON object")
    return raw


def _write_acceptance(path: Path, acceptance: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise IsolatedRoutePipelinePromotionReadinessAcceptanceError(
            "output filename must be isolated_route_pipeline_promotion_readiness_acceptance.json"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(acceptance, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Accept isolated route pipeline promotion readiness.")
    parser.add_argument(
        "--promotion-plan-audit",
        required=True,
        help="Path to isolated_route_pipeline_promotion_plan_audit.json.",
    )
    parser.add_argument("--output", help="Optional isolated_route_pipeline_promotion_readiness_acceptance.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    acceptance = accept_isolated_route_pipeline_promotion_readiness(
        promotion_plan_audit_path=Path(args.promotion_plan_audit),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(acceptance, indent=2, sort_keys=True))
    else:
        print(f"promotion_readiness_accepted: {acceptance['promotion_readiness_accepted']}")
        print(f"controlled_dev_smoke_ready: {acceptance['controlled_dev_smoke_ready']}")
        print(f"execution_allowed_by_0196: {acceptance['execution_allowed_by_0196']}")
        print(f"issues: {len(acceptance['issues'])}")
        print(f"warnings: {len(acceptance['warnings'])}")
    return 0 if acceptance["promotion_readiness_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
