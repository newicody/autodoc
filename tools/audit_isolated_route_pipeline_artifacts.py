#!/usr/bin/env python3
"""Audit isolated route pipeline smoke artifacts.

0191 is an artifact audit tool only.

It reads isolated_route_pipeline_smoke.json from 0190 and validates the related
JSON/JSONL artifacts produced by 0179 and 0184 through 0188.

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


ISOLATED_ROUTE_PIPELINE_ARTIFACT_AUDIT_SCHEMA = "missipy.route_pipeline.isolated_artifact_audit.v1"
EXPECTED_PIPELINE_SCHEMA = "missipy.route_pipeline.isolated_smoke.v1"
DEFAULT_OUTPUT_NAME = "isolated_route_pipeline_artifact_audit.json"

REQUIRED_ARTIFACTS = (
    "queue",
    "policy_scoped_queue",
    "route_request_to_command_plan",
    "command_builder_smoke",
    "isolated_handler_execution_plan",
    "isolated_handler_smoke",
    "isolated_handler_readback_smoke",
)


class IsolatedRoutePipelineArtifactAuditError(ValueError):
    """Raised when artifact audit inputs are unsafe."""


def audit_isolated_route_pipeline_artifacts(
    *,
    pipeline_report_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Audit a 0190 isolated route pipeline smoke report and artifacts."""

    report_path = Path(pipeline_report_path)
    pipeline = _read_json_file(report_path)
    issues: list[str] = []
    warnings: list[str] = []

    if pipeline.get("schema") != EXPECTED_PIPELINE_SCHEMA:
        issues.append("pipeline report schema mismatch")

    artifacts = pipeline.get("artifacts")
    if not isinstance(artifacts, Mapping):
        issues.append("pipeline artifacts must be an object")
        artifacts = {}

    artifact_status = _audit_artifact_paths(artifacts, issues)
    isolated_root = Path(str(pipeline.get("isolated_runtime_root") or ""))
    if not isolated_root.is_absolute():
        issues.append("isolated_runtime_root must be absolute")

    _audit_top_level_flags(pipeline, issues)
    _audit_counts(pipeline, issues)
    _audit_stage_reports(pipeline, artifacts, issues)

    queue_items = _read_jsonl_artifact(artifacts, "queue", warnings)
    scoped_queue_items = _read_jsonl_artifact(artifacts, "policy_scoped_queue", warnings)
    command_plan_items = _read_jsonl_artifact(artifacts, "route_request_to_command_plan", warnings)
    command_smoke_items = _read_jsonl_artifact(artifacts, "command_builder_smoke", warnings)
    isolated_plan_items = _read_jsonl_artifact(artifacts, "isolated_handler_execution_plan", warnings)
    handler_smoke_items = _read_jsonl_artifact(artifacts, "isolated_handler_smoke", warnings)
    readback_items = _read_jsonl_artifact(artifacts, "isolated_handler_readback_smoke", warnings)

    _audit_scoped_queue(policy_decision_id=str(pipeline.get("policy_decision_id")), scoped_queue_items=scoped_queue_items, issues=issues)
    _audit_item_counts(
        pipeline=pipeline,
        scoped_queue_items=scoped_queue_items,
        command_plan_items=command_plan_items,
        command_smoke_items=command_smoke_items,
        isolated_plan_items=isolated_plan_items,
        handler_smoke_items=handler_smoke_items,
        readback_items=readback_items,
        issues=issues,
    )
    _audit_handler_smoke_items(handler_smoke_items, isolated_root=isolated_root, issues=issues)
    _audit_readback_items(readback_items, isolated_root=isolated_root, issues=issues)

    audit = {
        "schema": ISOLATED_ROUTE_PIPELINE_ARTIFACT_AUDIT_SCHEMA,
        "pipeline_report_path": str(report_path),
        "pipeline_schema": pipeline.get("schema"),
        "pipeline_success": pipeline.get("pipeline_success"),
        "policy_decision_id": pipeline.get("policy_decision_id"),
        "runtime_root": pipeline.get("runtime_root"),
        "isolated_runtime_root": pipeline.get("isolated_runtime_root"),
        "artifact_status": artifact_status,
        "artifact_counts": {
            "queue_items": len(queue_items),
            "policy_scoped_queue_items": len(scoped_queue_items),
            "command_plan_items": len(command_plan_items),
            "command_smoke_items": len(command_smoke_items),
            "isolated_plan_items": len(isolated_plan_items),
            "handler_smoke_items": len(handler_smoke_items),
            "readback_items": len(readback_items),
        },
        "top_level_counts": {
            "queued_count": pipeline.get("queued_count"),
            "policy_scoped_queued_count": pipeline.get("policy_scoped_queued_count"),
            "command_plan_ready_count": pipeline.get("command_plan_ready_count"),
            "command_built_count": pipeline.get("command_built_count"),
            "handler_executed_count": pipeline.get("handler_executed_count"),
            "frames_written_count": pipeline.get("frames_written_count"),
            "readback_count": pipeline.get("readback_count"),
        },
        "issues": issues,
        "warnings": warnings,
        "audit_success": not issues,
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


def _audit_artifact_paths(artifacts: Mapping[str, Any], issues: list[str]) -> dict[str, dict[str, Any]]:
    status: dict[str, dict[str, Any]] = {}
    for key in REQUIRED_ARTIFACTS:
        raw = artifacts.get(key)
        exists = isinstance(raw, str) and Path(raw).exists()
        status[key] = {"path": raw, "exists": exists}
        if not exists:
            issues.append(f"missing artifact: {key}")
    return status


def _audit_top_level_flags(pipeline: Mapping[str, Any], issues: list[str]) -> None:
    expected_false = (
        "scheduler_modified",
        "eventbus_instantiated",
        "controlproxy_frames_written",
        "network_used",
    )
    for key in expected_false:
        if pipeline.get(key) is not False:
            issues.append(f"{key} must be false")
    if pipeline.get("pipeline_success") is not True:
        issues.append("pipeline_success must be true")


def _audit_counts(pipeline: Mapping[str, Any], issues: list[str]) -> None:
    names = (
        "queued_count",
        "policy_scoped_queued_count",
        "command_plan_ready_count",
        "command_built_count",
        "handler_executed_count",
        "frames_written_count",
        "readback_count",
    )
    values = {name: pipeline.get(name) for name in names}
    for name, value in values.items():
        if not isinstance(value, int) or value <= 0:
            issues.append(f"{name} must be a positive integer")
    scoped = values.get("policy_scoped_queued_count")
    for name in ("command_plan_ready_count", "command_built_count", "handler_executed_count", "frames_written_count", "readback_count"):
        if values.get(name) != scoped:
            issues.append(f"{name} must equal policy_scoped_queued_count")


def _audit_stage_reports(pipeline: Mapping[str, Any], artifacts: Mapping[str, Any], issues: list[str]) -> None:
    stage_reports = pipeline.get("stage_reports")
    if not isinstance(stage_reports, Mapping):
        issues.append("stage_reports must be an object")
        return
    plan = stage_reports.get("0184_route_request_to_command_plan")
    if not isinstance(plan, Mapping):
        issues.append("0184 stage report missing")
    elif plan.get("queue_path") != artifacts.get("policy_scoped_queue"):
        issues.append("0184 must read policy_scoped_queue")
    for stage_name, stage in stage_reports.items():
        if not isinstance(stage, Mapping):
            issues.append(f"{stage_name} stage report must be an object")
            continue
        if stage.get("scheduler_modified") is not False:
            issues.append(f"{stage_name} scheduler_modified must be false")
        if stage.get("controlproxy_frames_written") is True:
            issues.append(f"{stage_name} must not write ControlProxy frames")
        if stage.get("network_used") is True:
            issues.append(f"{stage_name} must not use network")


def _audit_scoped_queue(*, policy_decision_id: str, scoped_queue_items: list[dict[str, Any]], issues: list[str]) -> None:
    for index, item in enumerate(scoped_queue_items, start=1):
        if item.get("policy_decision_id") != policy_decision_id:
            issues.append(f"policy scoped queue item {index} has wrong policy_decision_id")


def _audit_item_counts(
    *,
    pipeline: Mapping[str, Any],
    scoped_queue_items: list[dict[str, Any]],
    command_plan_items: list[dict[str, Any]],
    command_smoke_items: list[dict[str, Any]],
    isolated_plan_items: list[dict[str, Any]],
    handler_smoke_items: list[dict[str, Any]],
    readback_items: list[dict[str, Any]],
    issues: list[str],
) -> None:
    expected = pipeline.get("policy_scoped_queued_count")
    for name, items in (
        ("policy_scoped_queue_items", scoped_queue_items),
        ("command_plan_items", command_plan_items),
        ("command_smoke_items", command_smoke_items),
        ("isolated_plan_items", isolated_plan_items),
        ("handler_smoke_items", handler_smoke_items),
        ("readback_items", readback_items),
    ):
        if len(items) != expected:
            issues.append(f"{name} must equal policy_scoped_queued_count")


def _audit_handler_smoke_items(items: list[dict[str, Any]], *, isolated_root: Path, issues: list[str]) -> None:
    for index, item in enumerate(items, start=1):
        if item.get("issues") not in ([], None):
            issues.append(f"handler smoke item {index} has issues")
        if item.get("handler_called") is not True:
            issues.append(f"handler smoke item {index} must call handler")
        if item.get("scheduler_modified") is not False:
            issues.append(f"handler smoke item {index} scheduler_modified must be false")
        if item.get("controlproxy_frames_written") is not False:
            issues.append(f"handler smoke item {index} must not write ControlProxy frames")
        for frame_path in item.get("frame_paths", []):
            path = Path(str(frame_path))
            if not _is_within(path, isolated_root):
                issues.append(f"handler smoke frame path {index} escaped isolated root")
            if not path.exists():
                issues.append(f"handler smoke frame path {index} does not exist")


def _audit_readback_items(items: list[dict[str, Any]], *, isolated_root: Path, issues: list[str]) -> None:
    for index, item in enumerate(items, start=1):
        if item.get("issues") not in ([], None):
            issues.append(f"readback item {index} has issues")
        if item.get("handler_called") is not False:
            issues.append(f"readback item {index} must not call handler")
        if item.get("writer_permits_requested") is not False:
            issues.append(f"readback item {index} must not request writer permits")
        if item.get("frames_written") is not False:
            issues.append(f"readback item {index} must not write frames")
        if item.get("scheduler_modified") is not False:
            issues.append(f"readback item {index} scheduler_modified must be false")
        written = set(str(value) for value in item.get("written_route_refs", []))
        frames = item.get("readback_frames", [])
        if len(frames) != item.get("readback_count"):
            issues.append(f"readback item {index} readback_count mismatch")
        for frame in frames:
            if not isinstance(frame, Mapping):
                issues.append(f"readback item {index} frame must be an object")
                continue
            if str(frame.get("route_ref")) not in written:
                issues.append(f"readback item {index} route_ref was not written")
        for frame_path in item.get("frame_paths", []):
            if not _is_within(Path(str(frame_path)), isolated_root):
                issues.append(f"readback frame path {index} escaped isolated root")


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise IsolatedRoutePipelineArtifactAuditError("pipeline report must be a JSON object")
    return raw


def _read_jsonl_artifact(artifacts: Mapping[str, Any], key: str, warnings: list[str]) -> list[dict[str, Any]]:
    path_raw = artifacts.get(key)
    if not isinstance(path_raw, str) or not Path(path_raw).exists():
        warnings.append(f"cannot read missing artifact: {key}")
        return []
    return list(_read_jsonl(Path(path_raw)))


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise IsolatedRoutePipelineArtifactAuditError(f"JSONL line must be object at {path}:{line_number}")
            yield value


def _write_audit(path: Path, audit: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise IsolatedRoutePipelineArtifactAuditError("output filename must be isolated_route_pipeline_artifact_audit.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit isolated route pipeline smoke artifacts.")
    parser.add_argument("--pipeline-report", required=True, help="Path to isolated_route_pipeline_smoke.json.")
    parser.add_argument("--output", help="Optional isolated_route_pipeline_artifact_audit.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    audit = audit_isolated_route_pipeline_artifacts(
        pipeline_report_path=Path(args.pipeline_report),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(f"audit_success: {audit['audit_success']}")
        print(f"issues: {len(audit['issues'])}")
        print(f"warnings: {len(audit['warnings'])}")
        print("handler_called: False")
        print("frames_written: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
