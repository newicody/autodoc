#!/usr/bin/env python3
"""Accept controlled dev RouteProxy smoke after P0199 execution.

0200 is the Bloc B post-execution audit, acceptance, registry, and coherence
patch.

It reads controlled_dev_routeproxy_smoke_execution.json from 0199, reuses the
existing isolated_route_pipeline_smoke.json produced by tools/run_isolated_route_pipeline_smoke.py,
and writes controlled_dev_routeproxy_smoke_post_execution_acceptance.json. It
can append controlled_dev_routeproxy_smoke_registry.jsonl.

It must reuse the existing 0199 execution report and existing pipeline artifacts.
It must not introduce a new runtime handler, adapter, bus, RouteProxy runtime,
ControlProxy runtime, SQL backend, Qdrant backend, GitHub client, graph
renderer, or inference path.

0200 does not execute controlled-dev-routeproxy-smoke.
0200 does not import runtime handler modules.
0200 does not call handle_scheduler_route_command.
0200 does not call handle_scheduler_route_request.
0200 does not call prepare_route_proxy_runtime.
0200 does not call read_route_frame.
0200 does not request writer permits.
0200 does not call write_route_frame.
0200 does not modify Scheduler.run.
0200 does not instantiate Scheduler.
0200 does not instantiate EventBus.
0200 does not write ControlProxy or RouteProxy frames.
0200 does not call GitHub API or use network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


CONTROLLED_DEV_POST_EXECUTION_ACCEPTANCE_SCHEMA = (
    "missipy.route_pipeline.controlled_dev_post_execution_acceptance.v1"
)
CONTROLLED_DEV_REGISTRY_ENTRY_SCHEMA = "missipy.route_pipeline.controlled_dev_registry_entry.v1"
EXPECTED_EXECUTION_SCHEMA = "missipy.route_pipeline.controlled_dev_routeproxy_smoke_execution.v1"
EXPECTED_PIPELINE_SCHEMA = "missipy.route_pipeline.isolated_smoke.v1"
EXPECTED_EXECUTION_TOOL = "tools/run_isolated_route_pipeline_smoke.py"
EXPECTED_ACCEPTED_BASELINE = "controlled-dev-routeproxy-write-read-v1"
DEFAULT_OUTPUT_NAME = "controlled_dev_routeproxy_smoke_post_execution_acceptance.json"
DEFAULT_REGISTRY_NAME = "controlled_dev_routeproxy_smoke_registry.jsonl"


class ControlledDevRouteProxySmokePostExecutionAcceptanceError(ValueError):
    """Raised when the controlled dev smoke post-execution acceptance is unsafe."""


def accept_controlled_dev_routeproxy_smoke_post_execution(
    *,
    execution_report_path: Path | str,
    output_path: Path | str | None = None,
    registry_path: Path | str | None = None,
) -> dict[str, Any]:
    """Audit and accept the P0199 controlled dev smoke execution without rerunning it."""

    execution_path = Path(execution_report_path)
    execution = _read_json_file(execution_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_execution_report(execution, issues, warnings)

    pipeline_path = Path(str(execution.get("pipeline_output", "")))
    pipeline: dict[str, Any] = {}
    if not pipeline_path.is_absolute():
        issues.append("pipeline_output must be absolute")
    elif not pipeline_path.exists():
        issues.append("pipeline_output must exist")
    else:
        pipeline = _read_json_file(pipeline_path)
        _audit_pipeline_output(pipeline, execution, issues, warnings)

    target_runtime_root = Path(str(execution.get("target_runtime_root", "")))
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be controlled_dev_routeproxy_smoke_post_execution_acceptance.json")
    if target_runtime_root.is_absolute() and final_output.is_absolute():
        if not _is_within_or_equal(final_output, target_runtime_root):
            issues.append("post-execution acceptance output must be inside target_runtime_root")

    selected_entry_digest = str(execution.get("selected_entry_digest") or "")
    source_baseline_ref = str(execution.get("selected_baseline_ref") or "")
    acceptance_seed = {
        "execution_report_path": str(execution_path),
        "pipeline_output": str(pipeline_path),
        "policy_decision_id": execution.get("policy_decision_id"),
        "target_runtime_root": execution.get("target_runtime_root"),
        "target_isolated_runtime_root": execution.get("target_isolated_runtime_root"),
        "frames_written_count": execution.get("frames_written_count"),
        "readback_count": execution.get("readback_count"),
        "source_selected_entry_digest": selected_entry_digest,
    }
    acceptance_digest = _stable_digest(acceptance_seed)
    controlled_dev_baseline_ref = f"baseline:{EXPECTED_ACCEPTED_BASELINE}:{acceptance_digest[:16]}"

    acceptance = {
        "schema": CONTROLLED_DEV_POST_EXECUTION_ACCEPTANCE_SCHEMA,
        "bloc": "B",
        "bloc_name": "controlled-dev-smoke",
        "bloc_patch_limit": 3,
        "bloc_patches": [
            "0198-controlled_dev_routeproxy_smoke_plan",
            "0199-controlled_dev_routeproxy_smoke_execution",
            "0200-controlled_dev_routeproxy_smoke_post_execution_acceptance",
        ],
        "execution_report_path": str(execution_path),
        "execution_report_schema": execution.get("schema"),
        "pipeline_output": str(pipeline_path),
        "pipeline_schema": pipeline.get("schema"),
        "source_baseline_ref": source_baseline_ref,
        "source_entry_digest": selected_entry_digest,
        "accepted_baseline": EXPECTED_ACCEPTED_BASELINE,
        "controlled_dev_baseline_ref": controlled_dev_baseline_ref,
        "acceptance_digest": acceptance_digest,
        "policy_decision_id": execution.get("policy_decision_id"),
        "target_runtime_root": execution.get("target_runtime_root"),
        "target_isolated_runtime_root": execution.get("target_isolated_runtime_root"),
        "execution_tool_reused": execution.get("execution_tool_reused"),
        "controlled_dev_smoke_accepted": not issues,
        "bloc_b_coherence_accepted": not issues,
        "bloc_b_complete": not issues,
        "phase_re_evaluated": True,
        "next_bloc": "C",
        "next_bloc_name": "scheduler-hook-controlled",
        "next_recommended_patch": "0201-scheduler_integration_surface_audit",
        "execution_was_required_and_performed": True,
        "execution_locks_released_for_phase": True,
        "execution_scope": execution.get("execution_scope"),
        "issues": issues,
        "warnings": warnings,
        "queued_count": execution.get("queued_count"),
        "policy_scoped_queued_count": execution.get("policy_scoped_queued_count"),
        "command_plan_ready_count": execution.get("command_plan_ready_count"),
        "command_built_count": execution.get("command_built_count"),
        "handler_executed_count": execution.get("handler_executed_count"),
        "frames_written_count": execution.get("frames_written_count"),
        "readback_count": execution.get("readback_count"),
        "existing_surfaces_reused": True,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "runtime_imports_executed_by_0200": False,
        "handler_called_by_0200": False,
        "routeproxy_prepared_by_0200": False,
        "read_route_frame_called_by_0200": False,
        "writer_permits_requested_by_0200": False,
        "frames_written_by_0200": False,
        "controlproxy_frames_written": bool(execution.get("controlproxy_frames_written")),
        "scheduler_modified": bool(execution.get("scheduler_modified")),
        "eventbus_instantiated": bool(execution.get("eventbus_instantiated")),
        "network_used": bool(execution.get("network_used")),
    }

    if registry_path is not None:
        registry = _build_registry_entry(acceptance)
        _append_registry(Path(registry_path), registry)
        acceptance["registry_path"] = str(Path(registry_path))
        acceptance["registry_entry_digest"] = registry["entry_digest"]

    if output_path is not None:
        _write_acceptance(final_output, acceptance)

    return acceptance


def _audit_execution_report(execution: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if execution.get("schema") != EXPECTED_EXECUTION_SCHEMA:
        issues.append("execution report schema mismatch")
    if execution.get("execution_success") is not True:
        issues.append("execution_success must be true")
    if execution.get("execution_allowed_by_0199") is not True:
        issues.append("execution_allowed_by_0199 must be true")
    if execution.get("execution_unlocked_by_p0199") is not True:
        issues.append("execution_unlocked_by_p0199 must be true")
    if execution.get("execution_tool_reused") != EXPECTED_EXECUTION_TOOL:
        issues.append("execution_tool_reused must be tools/run_isolated_route_pipeline_smoke.py")
    if execution.get("requires_p0200_post_execution_audit") is not True:
        issues.append("requires_p0200_post_execution_audit must be true")
    if execution.get("pipeline_success") is not True:
        issues.append("pipeline_success must be true")
    if execution.get("issues") not in ([], None):
        issues.append("execution issues must be empty")
    if isinstance(execution.get("warnings"), list) and execution.get("warnings"):
        warnings.extend(str(item) for item in execution.get("warnings", []))
    if execution.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    if execution.get("existing_pipeline_tool_executed") is not True:
        issues.append("existing_pipeline_tool_executed must be true")
    if execution.get("controlproxy_frames_written") is not False:
        issues.append("ControlProxy frames must not be written")
    if execution.get("scheduler_modified") is not False:
        issues.append("Scheduler must not be modified")
    if execution.get("eventbus_instantiated") is not False:
        issues.append("EventBus must not be instantiated")
    if execution.get("network_used") is not False:
        issues.append("network must not be used")
    if execution.get("frames_written_count") != 1:
        issues.append("frames_written_count must be 1")
    if execution.get("readback_count") != 1:
        issues.append("readback_count must be 1")
    if execution.get("queued_count") != execution.get("policy_scoped_queued_count"):
        issues.append("queued_count must match policy_scoped_queued_count")
    if not isinstance(execution.get("policy_decision_id"), str) or not execution.get("policy_decision_id"):
        issues.append("policy_decision_id must be present")
    _audit_target_paths(execution, issues)


def _audit_pipeline_output(
    pipeline: Mapping[str, Any],
    execution: Mapping[str, Any],
    issues: list[str],
    warnings: list[str],
) -> None:
    if pipeline.get("schema") != EXPECTED_PIPELINE_SCHEMA:
        issues.append("pipeline schema mismatch")
    if pipeline.get("pipeline_success") is not True:
        issues.append("pipeline output pipeline_success must be true")
    for key in (
        "queued_count",
        "policy_scoped_queued_count",
        "command_plan_ready_count",
        "command_built_count",
        "handler_executed_count",
        "frames_written_count",
        "readback_count",
    ):
        if pipeline.get(key) != execution.get(key):
            issues.append(f"pipeline {key} must match execution report")
    if pipeline.get("controlproxy_frames_written") is not False:
        issues.append("pipeline ControlProxy frames must not be written")
    if pipeline.get("scheduler_modified") is not False:
        issues.append("pipeline Scheduler must not be modified")
    if pipeline.get("eventbus_instantiated") is not False:
        issues.append("pipeline EventBus must not be instantiated")
    if pipeline.get("network_used") is not False:
        issues.append("pipeline network must not be used")
    artifacts = pipeline.get("artifacts")
    if not isinstance(artifacts, Mapping):
        issues.append("pipeline artifacts must be present")
        return
    for key in (
        "queue",
        "policy_scoped_queue",
        "route_request_to_command_plan",
        "command_builder_smoke",
        "isolated_handler_execution_plan",
        "isolated_handler_smoke",
        "isolated_handler_readback_smoke",
    ):
        raw = artifacts.get(key)
        if not isinstance(raw, str) or not raw:
            issues.append(f"pipeline artifact missing: {key}")
            continue
        path = Path(raw)
        if not path.exists():
            issues.append(f"pipeline artifact does not exist: {key}")
        target_runtime_root = Path(str(execution.get("target_runtime_root", "")))
        if target_runtime_root.is_absolute() and path.is_absolute():
            if not _is_within_or_equal(path, target_runtime_root):
                issues.append(f"pipeline artifact must be inside target_runtime_root: {key}")


def _audit_target_paths(execution: Mapping[str, Any], issues: list[str]) -> None:
    target_runtime_root = Path(str(execution.get("target_runtime_root", "")))
    target_isolated_runtime_root = Path(str(execution.get("target_isolated_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    if not target_isolated_runtime_root.is_absolute():
        issues.append("target_isolated_runtime_root must be absolute")
    if target_runtime_root == target_isolated_runtime_root:
        issues.append("target_runtime_root and target_isolated_runtime_root must be distinct")
    if target_runtime_root.is_absolute() and target_isolated_runtime_root.is_absolute():
        if not _is_within_or_equal(target_isolated_runtime_root, target_runtime_root):
            issues.append("target_isolated_runtime_root must be inside target_runtime_root")
    pipeline_output = Path(str(execution.get("pipeline_output", "")))
    if pipeline_output.is_absolute() and target_runtime_root.is_absolute():
        if not _is_within_or_equal(pipeline_output, target_runtime_root):
            issues.append("pipeline_output must be inside target_runtime_root")


def _build_registry_entry(acceptance: Mapping[str, Any]) -> dict[str, Any]:
    seed = {
        "schema": CONTROLLED_DEV_REGISTRY_ENTRY_SCHEMA,
        "accepted_baseline": acceptance.get("accepted_baseline"),
        "controlled_dev_baseline_ref": acceptance.get("controlled_dev_baseline_ref"),
        "acceptance_digest": acceptance.get("acceptance_digest"),
        "policy_decision_id": acceptance.get("policy_decision_id"),
        "target_runtime_root": acceptance.get("target_runtime_root"),
        "target_isolated_runtime_root": acceptance.get("target_isolated_runtime_root"),
        "frames_written_count": acceptance.get("frames_written_count"),
        "readback_count": acceptance.get("readback_count"),
    }
    digest = _stable_digest(seed)
    return {
        **seed,
        "entry_digest": digest,
        "entry_ref": f"controlled-dev-registry:{digest[:16]}",
    }


def _append_registry(path: Path, entry: Mapping[str, Any]) -> None:
    if path.name != DEFAULT_REGISTRY_NAME:
        raise ControlledDevRouteProxySmokePostExecutionAcceptanceError(
            "registry filename must be controlled_dev_routeproxy_smoke_registry.jsonl"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(entry), sort_keys=True) + "\n")


def _stable_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(value), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_within_or_equal(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ControlledDevRouteProxySmokePostExecutionAcceptanceError("input must be a JSON object")
    return raw


def _write_acceptance(path: Path, acceptance: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ControlledDevRouteProxySmokePostExecutionAcceptanceError(
            "output filename must be controlled_dev_routeproxy_smoke_post_execution_acceptance.json"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(acceptance, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Accept controlled dev RouteProxy smoke post-execution.")
    parser.add_argument("--execution", required=True, help="Path to controlled_dev_routeproxy_smoke_execution.json.")
    parser.add_argument("--output", help="Optional controlled_dev_routeproxy_smoke_post_execution_acceptance.json output path.")
    parser.add_argument("--registry", help="Optional controlled_dev_routeproxy_smoke_registry.jsonl append path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    acceptance = accept_controlled_dev_routeproxy_smoke_post_execution(
        execution_report_path=Path(args.execution),
        output_path=Path(args.output) if args.output else None,
        registry_path=Path(args.registry) if args.registry else None,
    )

    if args.format == "json":
        print(json.dumps(acceptance, indent=2, sort_keys=True))
    else:
        print(f"controlled_dev_smoke_accepted: {acceptance['controlled_dev_smoke_accepted']}")
        print(f"bloc_b_complete: {acceptance['bloc_b_complete']}")
        print(f"next_bloc: {acceptance['next_bloc']}")
        print(f"accepted_baseline: {acceptance['accepted_baseline']}")
        print(f"issues: {len(acceptance['issues'])}")
    return 0 if acceptance["controlled_dev_smoke_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
