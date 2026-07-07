#!/usr/bin/env python3
"""Plan controlled dev RouteProxy smoke from Bloc A coherence.

0198 is the Bloc B controlled dev smoke plan only.

It reads route_pipeline_bloc_a_coherence_record.json from 0197 and writes
controlled_dev_routeproxy_smoke_plan.json. It plans the first controlled dev
execution step for P0199 while reusing the existing isolated route pipeline
smoke tool.

It must reuse the existing 0197 Bloc A coherence artifact and the existing
tools/run_isolated_route_pipeline_smoke.py execution surface. It must not
introduce a new runtime handler, adapter, bus, RouteProxy runtime, ControlProxy
runtime, SQL backend, Qdrant backend, GitHub client, graph renderer, or
inference path.

Execution locks are phase gates, not permanent prohibitions.
P0199 may unlock controlled-dev-routeproxy-smoke explicitly.
P0198 itself does not execute controlled-dev-routeproxy-smoke.

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


CONTROLLED_DEV_ROUTE_PROXY_SMOKE_PLAN_SCHEMA = "missipy.route_pipeline.controlled_dev_routeproxy_smoke_plan.v1"
EXPECTED_BLOC_A_SCHEMA = "missipy.route_pipeline.bloc_a_coherence_record.v1"
EXPECTED_BASELINE = "isolated-route-pipeline-write-read-v1"
EXPECTED_PROMOTION_TARGET = "controlled-dev-routeproxy-smoke"
DEFAULT_OUTPUT_NAME = "controlled_dev_routeproxy_smoke_plan.json"

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


class ControlledDevRouteProxySmokePlanError(ValueError):
    """Raised when the controlled dev smoke plan cannot be built safely."""


def plan_controlled_dev_routeproxy_smoke(
    *,
    bloc_a_coherence_path: Path | str,
    policy_decision_id: str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build a controlled dev RouteProxy smoke plan without executing it."""

    path = Path(bloc_a_coherence_path)
    coherence = _read_json_file(path)
    issues: list[str] = []
    warnings: list[str] = []

    if coherence.get("schema") != EXPECTED_BLOC_A_SCHEMA:
        issues.append("Bloc A coherence schema mismatch")
    if coherence.get("bloc_a_coherence_accepted") is not True:
        issues.append("bloc_a_coherence_accepted must be true")
    if coherence.get("bloc_a_complete") is not True:
        issues.append("bloc_a_complete must be true")
    if coherence.get("phase_re_evaluated") is not True:
        issues.append("phase_re_evaluated must be true")
    if coherence.get("future_execution_can_be_unlocked") is not True:
        issues.append("future_execution_can_be_unlocked must be true")
    if coherence.get("execution_allowed_by_0197") is not False:
        issues.append("execution_allowed_by_0197 must remain false")
    if coherence.get("accepted_baseline") != EXPECTED_BASELINE:
        issues.append("accepted_baseline mismatch")
    if coherence.get("promotion_target") != EXPECTED_PROMOTION_TARGET:
        issues.append("promotion_target mismatch")
    if coherence.get("next_bloc") != "B":
        issues.append("next_bloc must be B")
    if coherence.get("issues") not in ([], None):
        issues.append("Bloc A coherence issues must be empty")
    if isinstance(coherence.get("warnings"), list) and coherence.get("warnings"):
        warnings.extend(str(item) for item in coherence.get("warnings", []))
    if coherence.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")

    _audit_policy_decision_id(policy_decision_id, issues)
    _audit_required_paths(coherence, issues)
    _audit_false_flags(coherence, FALSE_SAFETY_FLAGS, issues)
    _audit_false_flags(coherence, FALSE_NEW_SURFACE_FLAGS, issues)

    target_runtime_root = coherence.get("target_runtime_root")
    target_isolated_runtime_root = coherence.get("target_isolated_runtime_root")

    plan = {
        "schema": CONTROLLED_DEV_ROUTE_PROXY_SMOKE_PLAN_SCHEMA,
        "bloc": "B",
        "bloc_name": "controlled-dev-smoke",
        "bloc_patch_limit": 3,
        "bloc_a_coherence_path": str(path),
        "bloc_a_coherence_schema": coherence.get("schema"),
        "selected_baseline_ref": coherence.get("selected_baseline_ref"),
        "selected_entry_digest": coherence.get("selected_entry_digest"),
        "accepted_baseline": coherence.get("accepted_baseline"),
        "source_policy_decision_id": coherence.get("source_policy_decision_id"),
        "source_runtime_root": coherence.get("source_runtime_root"),
        "source_isolated_runtime_root": coherence.get("source_isolated_runtime_root"),
        "target_runtime_root": target_runtime_root,
        "target_isolated_runtime_root": target_isolated_runtime_root,
        "promotion_target": coherence.get("promotion_target"),
        "policy_decision_id": policy_decision_id,
        "plan_ready": not issues,
        "execution_allowed_by_0198": False,
        "execution_can_be_unlocked_by_p0199": not issues,
        "execution_unlock_planned_for": "0199-controlled_dev_routeproxy_smoke_execution",
        "execution_tool_to_reuse": "tools/run_isolated_route_pipeline_smoke.py",
        "required_inputs_for_p0199": [
            "context.bus.jsonl with one eligible route request candidate",
            "explicit policy_decision_id from this plan",
            "target_runtime_root from this plan",
            "target_isolated_runtime_root from this plan",
        ],
        "required_outputs_for_p0199": [
            "isolated_route_pipeline_smoke.json under target_runtime_root",
            "scheduler.route_requests.policy_scoped.jsonl under target_runtime_root",
            "isolated_scheduler_route_handler_smoke.jsonl under target_runtime_root",
            "isolated_scheduler_route_handler_readback_smoke.jsonl under target_runtime_root",
        ],
        "required_followup_for_p0200": [
            "post-execution artifact audit",
            "post-audit acceptance gate",
            "controlled-dev baseline registry append or bloc-level acceptance record",
        ],
        "execution_constraints_for_p0199": [
            "reuse tools/run_isolated_route_pipeline_smoke.py before adding new execution code",
            "do not modify Scheduler.run",
            "do not write ControlProxy frames",
            "write RouteProxy frames only under target_isolated_runtime_root",
            "keep scheduler.route_requests.jsonl append-only",
            "use fresh scheduler.route_requests.policy_scoped.jsonl for the policy_decision_id",
            "no GitHub API or network",
            "no SQL or Qdrant writes",
            "update docs, graph, changelog, manifest, and rule",
        ],
        "coherence_decisions": [
            "Bloc B is the first execution-oriented bloc.",
            "P0198 remains a plan and does not execute.",
            "P0199 may explicitly unlock controlled dev execution when it reuses existing surfaces.",
            "Execution locks are phase gates, not permanent prohibitions.",
            "Prototype progress requires execution, followed by audit and acceptance.",
        ],
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
    }

    if output_path is not None:
        _write_plan(Path(output_path), plan)

    return plan


def _audit_policy_decision_id(policy_decision_id: str, issues: list[str]) -> None:
    if not isinstance(policy_decision_id, str) or not policy_decision_id:
        issues.append("policy_decision_id must be present")
        return
    if not policy_decision_id.startswith("policy:allow:"):
        issues.append("policy_decision_id must start with policy:allow:")
    if "0199" not in policy_decision_id and "controlled-dev" not in policy_decision_id:
        issues.append("policy_decision_id should identify the controlled dev execution scope")


def _audit_required_paths(coherence: Mapping[str, Any], issues: list[str]) -> None:
    for key in (
        "target_runtime_root",
        "target_isolated_runtime_root",
        "source_runtime_root",
        "source_isolated_runtime_root",
    ):
        if not isinstance(coherence.get(key), str) or not coherence.get(key):
            issues.append(f"{key} must be present")

    target_runtime_root = coherence.get("target_runtime_root")
    target_isolated_runtime_root = coherence.get("target_isolated_runtime_root")
    if isinstance(target_runtime_root, str) and isinstance(target_isolated_runtime_root, str):
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


def _audit_false_flags(coherence: Mapping[str, Any], flags: tuple[str, ...], issues: list[str]) -> None:
    for flag in flags:
        if coherence.get(flag) is not False:
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
        raise ControlledDevRouteProxySmokePlanError("Bloc A coherence record must be a JSON object")
    return raw


def _write_plan(path: Path, plan: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ControlledDevRouteProxySmokePlanError("output filename must be controlled_dev_routeproxy_smoke_plan.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan controlled dev RouteProxy smoke.")
    parser.add_argument("--bloc-a-coherence", required=True, help="Path to route_pipeline_bloc_a_coherence_record.json.")
    parser.add_argument("--policy-decision-id", required=True, help="Explicit policy decision id for the P0199 execution scope.")
    parser.add_argument("--output", help="Optional controlled_dev_routeproxy_smoke_plan.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    plan = plan_controlled_dev_routeproxy_smoke(
        bloc_a_coherence_path=Path(args.bloc_a_coherence),
        policy_decision_id=args.policy_decision_id,
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"plan_ready: {plan['plan_ready']}")
        print(f"execution_allowed_by_0198: {plan['execution_allowed_by_0198']}")
        print(f"execution_can_be_unlocked_by_p0199: {plan['execution_can_be_unlocked_by_p0199']}")
        print(f"execution_tool_to_reuse: {plan['execution_tool_to_reuse']}")
        print(f"issues: {len(plan['issues'])}")
    return 0 if plan["plan_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
