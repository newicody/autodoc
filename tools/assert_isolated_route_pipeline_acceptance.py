#!/usr/bin/env python3
"""Assert acceptance of the isolated route pipeline prototype.

0192 is an acceptance gate only.

It reads isolated_route_pipeline_artifact_audit.json from 0191 and produces a
compact isolated_route_pipeline_acceptance.json verdict.

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


ISOLATED_ROUTE_PIPELINE_ACCEPTANCE_SCHEMA = "missipy.route_pipeline.isolated_acceptance.v1"
EXPECTED_AUDIT_SCHEMA = "missipy.route_pipeline.isolated_artifact_audit.v1"
DEFAULT_OUTPUT_NAME = "isolated_route_pipeline_acceptance.json"

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

DOWNSTREAM_TOP_LEVEL_COUNTS = (
    "command_plan_ready_count",
    "command_built_count",
    "handler_executed_count",
    "frames_written_count",
    "readback_count",
)

DOWNSTREAM_ARTIFACT_COUNTS = (
    "command_plan_items",
    "command_smoke_items",
    "isolated_plan_items",
    "handler_smoke_items",
    "readback_items",
)


class IsolatedRoutePipelineAcceptanceError(ValueError):
    """Raised when acceptance inputs are unsafe."""


def assert_isolated_route_pipeline_acceptance(
    *,
    audit_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build an acceptance verdict from a 0191 artifact audit."""

    path = Path(audit_path)
    audit = _read_json_file(path)
    issues: list[str] = []
    warnings: list[str] = []

    if audit.get("schema") != EXPECTED_AUDIT_SCHEMA:
        issues.append("audit schema mismatch")
    if audit.get("audit_success") is not True:
        issues.append("audit_success must be true")
    if audit.get("pipeline_success") is not True:
        issues.append("pipeline_success must be true")
    if audit.get("issues") not in ([], None):
        issues.append("audit issues must be empty")
    if audit.get("warnings") not in ([], None):
        warnings.append("audit warnings are present")

    for flag in FALSE_SAFETY_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")

    top_level_counts = audit.get("top_level_counts")
    artifact_counts = audit.get("artifact_counts")
    if not isinstance(top_level_counts, Mapping):
        issues.append("top_level_counts must be an object")
        top_level_counts = {}
    if not isinstance(artifact_counts, Mapping):
        issues.append("artifact_counts must be an object")
        artifact_counts = {}

    policy_scoped_count = top_level_counts.get("policy_scoped_queued_count")
    if not isinstance(policy_scoped_count, int) or policy_scoped_count <= 0:
        issues.append("policy_scoped_queued_count must be a positive integer")
        policy_scoped_count = None

    _assert_top_level_counts(top_level_counts, policy_scoped_count, issues)
    _assert_artifact_counts(artifact_counts, policy_scoped_count, issues)

    verdict = {
        "schema": ISOLATED_ROUTE_PIPELINE_ACCEPTANCE_SCHEMA,
        "audit_path": str(path),
        "pipeline_report_path": audit.get("pipeline_report_path"),
        "pipeline_schema": audit.get("pipeline_schema"),
        "policy_decision_id": audit.get("policy_decision_id"),
        "runtime_root": audit.get("runtime_root"),
        "isolated_runtime_root": audit.get("isolated_runtime_root"),
        "top_level_counts": dict(top_level_counts),
        "artifact_counts": dict(artifact_counts),
        "issues": issues,
        "warnings": warnings,
        "acceptance_approved": not issues,
        "accepted_baseline": "isolated-route-pipeline-write-read-v1" if not issues else None,
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
        _write_acceptance(Path(output_path), verdict)

    return verdict


def _assert_top_level_counts(
    counts: Mapping[str, Any],
    policy_scoped_count: int | None,
    issues: list[str],
) -> None:
    if policy_scoped_count is None:
        return
    queued = counts.get("queued_count")
    if not isinstance(queued, int) or queued <= 0:
        issues.append("queued_count must be a positive integer")
    for name in DOWNSTREAM_TOP_LEVEL_COUNTS:
        if counts.get(name) != policy_scoped_count:
            issues.append(f"{name} must equal policy_scoped_queued_count")


def _assert_artifact_counts(
    counts: Mapping[str, Any],
    policy_scoped_count: int | None,
    issues: list[str],
) -> None:
    if policy_scoped_count is None:
        return
    queue_items = counts.get("queue_items")
    if not isinstance(queue_items, int) or queue_items < policy_scoped_count:
        issues.append("queue_items must be >= policy_scoped_queued_count")
    if counts.get("policy_scoped_queue_items") != policy_scoped_count:
        issues.append("policy_scoped_queue_items must equal policy_scoped_queued_count")
    for name in DOWNSTREAM_ARTIFACT_COUNTS:
        if counts.get(name) != policy_scoped_count:
            issues.append(f"{name} must equal policy_scoped_queued_count")


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise IsolatedRoutePipelineAcceptanceError("audit must be a JSON object")
    return raw


def _write_acceptance(path: Path, verdict: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise IsolatedRoutePipelineAcceptanceError("output filename must be isolated_route_pipeline_acceptance.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assert isolated route pipeline acceptance from 0191 audit.")
    parser.add_argument("--audit", required=True, help="Path to isolated_route_pipeline_artifact_audit.json.")
    parser.add_argument("--output", help="Optional isolated_route_pipeline_acceptance.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    verdict = assert_isolated_route_pipeline_acceptance(
        audit_path=Path(args.audit),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(verdict, indent=2, sort_keys=True))
    else:
        print(f"acceptance_approved: {verdict['acceptance_approved']}")
        print(f"accepted_baseline: {verdict['accepted_baseline']}")
        print(f"issues: {len(verdict['issues'])}")
        print(f"warnings: {len(verdict['warnings'])}")
    return 0 if verdict["acceptance_approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
