#!/usr/bin/env python3
"""Audit isolated route pipeline promotion plan.

0195 is a promotion plan audit tool only.

It reads isolated_route_pipeline_promotion_plan.json from 0194 and validates
that the plan is coherent, scoped to controlled-dev-routeproxy-smoke, and ready
for a later controlled dev smoke.

It must reuse the existing 0194 promotion plan artifact.
It must not introduce a new runtime handler, adapter, bus, RouteProxy runtime,
ControlProxy runtime, SQL backend, Qdrant backend, GitHub client, graph renderer,
or inference path.

It does not execute the promotion.
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


ISOLATED_ROUTE_PIPELINE_PROMOTION_PLAN_AUDIT_SCHEMA = "missipy.route_pipeline.isolated_promotion_plan_audit.v1"
EXPECTED_PROMOTION_PLAN_SCHEMA = "missipy.route_pipeline.isolated_promotion_plan.v1"
EXPECTED_BASELINE = "isolated-route-pipeline-write-read-v1"
EXPECTED_PROMOTION_TARGET = "controlled-dev-routeproxy-smoke"
DEFAULT_OUTPUT_NAME = "isolated_route_pipeline_promotion_plan_audit.json"

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

REQUIRED_PRECONDITION_FRAGMENTS = (
    "policy_decision_id",
    "scheduler.route_requests.policy_scoped.jsonl",
    "scheduler.route_requests.jsonl append-only",
    "0189 pipeline",
    "0191 artifact audit",
    "0192 acceptance gate",
    "production route roots",
)

REQUIRED_PLANNED_STEPS = (
    "dev-smoke-run",
    "artifact-audit",
    "acceptance-gate",
    "baseline-registry",
)


class IsolatedRoutePipelinePromotionPlanAuditError(ValueError):
    """Raised when a promotion plan audit input is unsafe."""


def audit_isolated_route_pipeline_promotion_plan(
    *,
    promotion_plan_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Audit a 0194 promotion plan without executing it."""

    path = Path(promotion_plan_path)
    plan = _read_json_file(path)
    issues: list[str] = []
    warnings: list[str] = []

    if plan.get("schema") != EXPECTED_PROMOTION_PLAN_SCHEMA:
        issues.append("promotion plan schema mismatch")
    if plan.get("accepted_baseline") != EXPECTED_BASELINE:
        issues.append("accepted baseline mismatch")
    if plan.get("promotion_target") != EXPECTED_PROMOTION_TARGET:
        issues.append("promotion target mismatch")
    if plan.get("promotion_ready") is not True:
        issues.append("promotion_ready must be true")
    if plan.get("promotion_allowed_by_0194") is not False:
        issues.append("promotion_allowed_by_0194 must remain false")
    if not isinstance(plan.get("selected_baseline_ref"), str) or not plan.get("selected_baseline_ref"):
        issues.append("selected_baseline_ref must be present")
    if not isinstance(plan.get("selected_entry_digest"), str) or not plan.get("selected_entry_digest"):
        issues.append("selected_entry_digest must be present")
    if plan.get("issues") not in ([], None):
        issues.append("promotion plan issues must be empty")
    if isinstance(plan.get("warnings"), list) and plan.get("warnings"):
        warnings.extend(str(item) for item in plan.get("warnings", []))

    _audit_target_roots(plan, issues, warnings)
    _audit_preconditions(plan, issues)
    _audit_planned_steps(plan, issues)
    _audit_safety_flags(plan, issues)

    audit = {
        "schema": ISOLATED_ROUTE_PIPELINE_PROMOTION_PLAN_AUDIT_SCHEMA,
        "promotion_plan_path": str(path),
        "promotion_plan_schema": plan.get("schema"),
        "selected_baseline_ref": plan.get("selected_baseline_ref"),
        "selected_entry_digest": plan.get("selected_entry_digest"),
        "accepted_baseline": plan.get("accepted_baseline"),
        "source_policy_decision_id": plan.get("source_policy_decision_id"),
        "source_runtime_root": plan.get("source_runtime_root"),
        "source_isolated_runtime_root": plan.get("source_isolated_runtime_root"),
        "target_runtime_root": plan.get("target_runtime_root"),
        "target_isolated_runtime_root": plan.get("target_isolated_runtime_root"),
        "promotion_target": plan.get("promotion_target"),
        "promotion_ready": plan.get("promotion_ready"),
        "promotion_allowed_by_0194": plan.get("promotion_allowed_by_0194"),
        "planned_step_count": len(plan.get("planned_steps", [])) if isinstance(plan.get("planned_steps"), list) else 0,
        "required_precondition_count": len(plan.get("required_preconditions", [])) if isinstance(plan.get("required_preconditions"), list) else 0,
        "issues": issues,
        "warnings": warnings,
        "audit_success": not issues,
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
    }

    if output_path is not None:
        _write_audit(Path(output_path), audit)

    return audit


def _audit_target_roots(plan: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    raw_runtime = plan.get("target_runtime_root")
    raw_route = plan.get("target_isolated_runtime_root")
    if not isinstance(raw_runtime, str) or not raw_runtime:
        issues.append("target_runtime_root must be present")
        return
    if not isinstance(raw_route, str) or not raw_route:
        issues.append("target_isolated_runtime_root must be present")
        return

    target_runtime_root = Path(raw_runtime)
    target_isolated_runtime_root = Path(raw_route)

    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    if not target_isolated_runtime_root.is_absolute():
        issues.append("target_isolated_runtime_root must be absolute")
    if target_runtime_root == target_isolated_runtime_root:
        issues.append("target_runtime_root and target_isolated_runtime_root must be distinct")
    if _is_forbidden_root(target_runtime_root):
        issues.append("target_runtime_root is forbidden")
    if _is_forbidden_root(target_isolated_runtime_root):
        issues.append("target_isolated_runtime_root is forbidden")
    if target_runtime_root.is_absolute() and target_isolated_runtime_root.is_absolute():
        if not _is_within_or_equal(target_isolated_runtime_root, target_runtime_root):
            issues.append("target_isolated_runtime_root must be inside target_runtime_root")
        if any(part in {"prod", "production"} for part in target_runtime_root.parts):
            warnings.append("target_runtime_root contains production-like path segment")
        if any(part in {"prod", "production"} for part in target_isolated_runtime_root.parts):
            warnings.append("target_isolated_runtime_root contains production-like path segment")


def _audit_preconditions(plan: Mapping[str, Any], issues: list[str]) -> None:
    raw = plan.get("required_preconditions")
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        issues.append("required_preconditions must be a list of strings")
        return
    joined = "\n".join(raw)
    for fragment in REQUIRED_PRECONDITION_FRAGMENTS:
        if fragment not in joined:
            issues.append(f"missing required precondition fragment: {fragment}")


def _audit_planned_steps(plan: Mapping[str, Any], issues: list[str]) -> None:
    raw = plan.get("planned_steps")
    if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
        issues.append("planned_steps must be a list of objects")
        return
    by_step = {str(item.get("step")): item for item in raw}
    for step in REQUIRED_PLANNED_STEPS:
        if step not in by_step:
            issues.append(f"missing planned step: {step}")

    dev_step = by_step.get("dev-smoke-run")
    if isinstance(dev_step, Mapping):
        if dev_step.get("tool") != "tools/run_isolated_route_pipeline_smoke.py":
            issues.append("dev-smoke-run must reuse tools/run_isolated_route_pipeline_smoke.py")
        if dev_step.get("runtime_writes_allowed") is not True:
            issues.append("dev-smoke-run must be the only runtime-write planned step")
        if dev_step.get("routeproxy_frames_allowed") != "target_isolated_runtime_root only":
            issues.append("dev-smoke-run must restrict RouteProxy frames to target_isolated_runtime_root only")
        if dev_step.get("scheduler_run_modified") is not False:
            issues.append("dev-smoke-run must not modify Scheduler.run")
        if dev_step.get("controlproxy_frames_written") is not False:
            issues.append("dev-smoke-run must not write ControlProxy frames")

    for step_name, step in by_step.items():
        if step_name != "dev-smoke-run" and step.get("runtime_writes_allowed") is not False:
            issues.append(f"{step_name} must not allow runtime writes")
        if step.get("scheduler_run_modified") is not False:
            issues.append(f"{step_name} must not modify Scheduler.run")
        if step.get("controlproxy_frames_written") is not False:
            issues.append(f"{step_name} must not write ControlProxy frames")


def _audit_safety_flags(plan: Mapping[str, Any], issues: list[str]) -> None:
    for flag in FALSE_SAFETY_FLAGS:
        if plan.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _is_forbidden_root(path: Path) -> bool:
    resolved = path.resolve()
    forbidden = {
        Path("/"),
        Path("/dev"),
        Path("/dev/shm"),
        Path("/proc"),
        Path("/sys"),
        Path("/run"),
    }
    return resolved in forbidden


def _is_within_or_equal(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise IsolatedRoutePipelinePromotionPlanAuditError("promotion plan must be a JSON object")
    return raw


def _write_audit(path: Path, audit: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise IsolatedRoutePipelinePromotionPlanAuditError(
            "output filename must be isolated_route_pipeline_promotion_plan_audit.json"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit isolated route pipeline promotion plan.")
    parser.add_argument("--promotion-plan", required=True, help="Path to isolated_route_pipeline_promotion_plan.json.")
    parser.add_argument("--output", help="Optional isolated_route_pipeline_promotion_plan_audit.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    audit = audit_isolated_route_pipeline_promotion_plan(
        promotion_plan_path=Path(args.promotion_plan),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(f"audit_success: {audit['audit_success']}")
        print(f"promotion_ready: {audit['promotion_ready']}")
        print(f"promotion_allowed_by_0194: {audit['promotion_allowed_by_0194']}")
        print(f"issues: {len(audit['issues'])}")
        print(f"warnings: {len(audit['warnings'])}")
    return 0 if audit["audit_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
