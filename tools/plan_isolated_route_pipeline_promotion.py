#!/usr/bin/env python3
"""Plan promotion from accepted isolated baseline to controlled dev smoke.

0194 is a promotion planning tool only.

It reads isolated_route_pipeline_baseline_registry.jsonl from 0193 and writes a
controlled isolated_route_pipeline_promotion_plan.json. The plan describes the
next safe move from the accepted isolated prototype baseline toward a controlled
dev runtime smoke.

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
from typing import Any, Iterable, Mapping


ISOLATED_ROUTE_PIPELINE_PROMOTION_PLAN_SCHEMA = "missipy.route_pipeline.isolated_promotion_plan.v1"
EXPECTED_REGISTRY_ENTRY_SCHEMA = "missipy.route_pipeline.isolated_baseline_registry_entry.v1"
EXPECTED_BASELINE = "isolated-route-pipeline-write-read-v1"
DEFAULT_OUTPUT_NAME = "isolated_route_pipeline_promotion_plan.json"


class IsolatedRoutePipelinePromotionPlanError(ValueError):
    """Raised when a promotion plan cannot be built safely."""


def build_isolated_route_pipeline_promotion_plan(
    *,
    registry_path: Path | str,
    baseline_ref: str | None = None,
    target_runtime_root: Path | str,
    target_isolated_runtime_root: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build a promotion plan from the accepted baseline registry."""

    registry = Path(registry_path)
    entries = list(_read_registry_entries(registry))
    selected = _select_entry(entries, baseline_ref=baseline_ref)
    issues: list[str] = []
    warnings: list[str] = []

    target_root = Path(target_runtime_root)
    target_route_root = Path(target_isolated_runtime_root)
    if not target_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    if not target_route_root.is_absolute():
        issues.append("target_isolated_runtime_root must be absolute")
    if _is_forbidden_runtime_root(target_route_root):
        issues.append("target_isolated_runtime_root is forbidden")
    if target_root == target_route_root:
        issues.append("target_runtime_root and target_isolated_runtime_root must be distinct")
    if target_route_root != target_root and not _is_within_or_equal(target_route_root, target_root):
        warnings.append("target_isolated_runtime_root is outside target_runtime_root")

    _validate_selected_entry(selected, issues)

    plan = {
        "schema": ISOLATED_ROUTE_PIPELINE_PROMOTION_PLAN_SCHEMA,
        "registry_path": str(registry),
        "selected_baseline_ref": selected.get("baseline_ref"),
        "selected_entry_digest": selected.get("entry_digest"),
        "accepted_baseline": selected.get("accepted_baseline"),
        "source_policy_decision_id": selected.get("policy_decision_id"),
        "source_runtime_root": selected.get("runtime_root"),
        "source_isolated_runtime_root": selected.get("isolated_runtime_root"),
        "target_runtime_root": str(target_root),
        "target_isolated_runtime_root": str(target_route_root),
        "promotion_target": "controlled-dev-routeproxy-smoke",
        "promotion_allowed_by_0194": False,
        "promotion_ready": not issues,
        "issues": issues,
        "warnings": warnings,
        "required_preconditions": [
            "Use an explicit new policy_decision_id for the controlled dev smoke.",
            "Use a fresh scheduler.route_requests.policy_scoped.jsonl for the target run.",
            "Keep scheduler.route_requests.jsonl append-only.",
            "Run the 0189 pipeline only against target_runtime_root and target_isolated_runtime_root.",
            "Run 0191 artifact audit after the controlled dev smoke.",
            "Run 0192 acceptance gate after audit.",
            "Do not promote to production route roots from 0194.",
        ],
        "planned_steps": [
            {
                "step": "dev-smoke-run",
                "tool": "tools/run_isolated_route_pipeline_smoke.py",
                "runtime_writes_allowed": True,
                "routeproxy_frames_allowed": "target_isolated_runtime_root only",
                "scheduler_run_modified": False,
                "controlproxy_frames_written": False,
            },
            {
                "step": "artifact-audit",
                "tool": "tools/audit_isolated_route_pipeline_artifacts.py",
                "runtime_writes_allowed": False,
                "routeproxy_frames_allowed": False,
                "scheduler_run_modified": False,
                "controlproxy_frames_written": False,
            },
            {
                "step": "acceptance-gate",
                "tool": "tools/assert_isolated_route_pipeline_acceptance.py",
                "runtime_writes_allowed": False,
                "routeproxy_frames_allowed": False,
                "scheduler_run_modified": False,
                "controlproxy_frames_written": False,
            },
            {
                "step": "baseline-registry",
                "tool": "tools/register_isolated_route_pipeline_baseline.py",
                "runtime_writes_allowed": False,
                "routeproxy_frames_allowed": False,
                "scheduler_run_modified": False,
                "controlproxy_frames_written": False,
            },
        ],
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
        _write_plan(Path(output_path), plan)

    return plan


def _validate_selected_entry(entry: Mapping[str, Any], issues: list[str]) -> None:
    if entry.get("schema") != EXPECTED_REGISTRY_ENTRY_SCHEMA:
        issues.append("registry entry schema mismatch")
    if entry.get("accepted_baseline") != EXPECTED_BASELINE:
        issues.append("accepted baseline mismatch")
    top_counts = entry.get("top_level_counts")
    artifact_counts = entry.get("artifact_counts")
    safety_flags = entry.get("safety_flags")
    if not isinstance(top_counts, Mapping):
        issues.append("top_level_counts must be an object")
        top_counts = {}
    if not isinstance(artifact_counts, Mapping):
        issues.append("artifact_counts must be an object")
        artifact_counts = {}
    if not isinstance(safety_flags, Mapping):
        issues.append("safety_flags must be an object")
        safety_flags = {}
    scoped = top_counts.get("policy_scoped_queued_count")
    if not isinstance(scoped, int) or scoped <= 0:
        issues.append("policy_scoped_queued_count must be positive")
    for name in (
        "command_plan_ready_count",
        "command_built_count",
        "handler_executed_count",
        "frames_written_count",
        "readback_count",
    ):
        if top_counts.get(name) != scoped:
            issues.append(f"{name} must equal policy_scoped_queued_count")
    for name in (
        "policy_scoped_queue_items",
        "command_plan_items",
        "command_smoke_items",
        "isolated_plan_items",
        "handler_smoke_items",
        "readback_items",
    ):
        if artifact_counts.get(name) != scoped:
            issues.append(f"{name} must equal policy_scoped_queued_count")
    for flag, value in safety_flags.items():
        if value is not False:
            issues.append(f"safety flag must be false: {flag}")


def _select_entry(entries: list[dict[str, Any]], *, baseline_ref: str | None) -> dict[str, Any]:
    if not entries:
        raise IsolatedRoutePipelinePromotionPlanError("baseline registry is empty")
    if baseline_ref is not None:
        for entry in entries:
            if entry.get("baseline_ref") == baseline_ref:
                return entry
        raise IsolatedRoutePipelinePromotionPlanError("requested baseline_ref not found")
    return entries[-1]


def _read_registry_entries(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise IsolatedRoutePipelinePromotionPlanError(f"registry line must be an object at {path}:{line_number}")
            yield value


def _is_forbidden_runtime_root(path: Path) -> bool:
    resolved = path.resolve()
    return resolved in {
        Path("/"),
        Path("/dev"),
        Path("/dev/shm"),
        Path("/proc"),
        Path("/sys"),
        Path("/run"),
    }


def _is_within_or_equal(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _write_plan(path: Path, plan: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise IsolatedRoutePipelinePromotionPlanError("output filename must be isolated_route_pipeline_promotion_plan.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan promotion from accepted isolated baseline to controlled dev smoke.")
    parser.add_argument("--registry", required=True, help="Path to isolated_route_pipeline_baseline_registry.jsonl.")
    parser.add_argument("--baseline-ref", help="Optional explicit baseline_ref to promote from.")
    parser.add_argument("--target-runtime-root", required=True, help="Absolute target runtime root for the planned dev smoke.")
    parser.add_argument("--target-isolated-runtime-root", required=True, help="Absolute target RouteProxy root for the planned dev smoke.")
    parser.add_argument("--output", help="Optional isolated_route_pipeline_promotion_plan.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    plan = build_isolated_route_pipeline_promotion_plan(
        registry_path=Path(args.registry),
        baseline_ref=args.baseline_ref,
        target_runtime_root=Path(args.target_runtime_root),
        target_isolated_runtime_root=Path(args.target_isolated_runtime_root),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"promotion_ready: {plan['promotion_ready']}")
        print(f"promotion_allowed_by_0194: {plan['promotion_allowed_by_0194']}")
        print(f"selected_baseline_ref: {plan['selected_baseline_ref']}")
        print(f"issues: {len(plan['issues'])}")
        print(f"warnings: {len(plan['warnings'])}")
    return 0 if plan["promotion_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
