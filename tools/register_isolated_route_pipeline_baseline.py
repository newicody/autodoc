#!/usr/bin/env python3
"""Register an accepted isolated route pipeline baseline.

0193 is a baseline registry tool only.

It reads isolated_route_pipeline_acceptance.json from 0192 and writes a compact
isolated_route_pipeline_baseline_registry.jsonl entry. The registry is an audit
index for accepted isolated prototypes.

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
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ISOLATED_ROUTE_PIPELINE_BASELINE_REGISTRY_SCHEMA = "missipy.route_pipeline.isolated_baseline_registry.v1"
ISOLATED_ROUTE_PIPELINE_BASELINE_REGISTRY_ENTRY_SCHEMA = "missipy.route_pipeline.isolated_baseline_registry_entry.v1"
EXPECTED_ACCEPTANCE_SCHEMA = "missipy.route_pipeline.isolated_acceptance.v1"
EXPECTED_ACCEPTED_BASELINE = "isolated-route-pipeline-write-read-v1"
DEFAULT_OUTPUT_NAME = "isolated_route_pipeline_baseline_registry.jsonl"


class IsolatedRoutePipelineBaselineRegistryError(ValueError):
    """Raised when an accepted baseline cannot be registered safely."""


def register_isolated_route_pipeline_baseline(
    *,
    acceptance_path: Path | str,
    output_path: Path | str,
    append: bool = False,
) -> dict[str, Any]:
    """Register an accepted isolated route pipeline baseline in JSONL."""

    acceptance_file = Path(acceptance_path)
    acceptance = _read_json_file(acceptance_file)
    issues: list[str] = []

    if acceptance.get("schema") != EXPECTED_ACCEPTANCE_SCHEMA:
        issues.append("acceptance schema mismatch")
    if acceptance.get("acceptance_approved") is not True:
        issues.append("acceptance_approved must be true")
    if acceptance.get("accepted_baseline") != EXPECTED_ACCEPTED_BASELINE:
        issues.append("accepted_baseline mismatch")
    if acceptance.get("issues") not in ([], None):
        issues.append("acceptance issues must be empty")
    if acceptance.get("warnings") not in ([], None):
        issues.append("acceptance warnings must be empty")

    _assert_false_flags(acceptance, issues)
    top_level_counts = acceptance.get("top_level_counts")
    artifact_counts = acceptance.get("artifact_counts")
    if not isinstance(top_level_counts, Mapping):
        issues.append("top_level_counts must be an object")
        top_level_counts = {}
    if not isinstance(artifact_counts, Mapping):
        issues.append("artifact_counts must be an object")
        artifact_counts = {}

    scoped_count = top_level_counts.get("policy_scoped_queued_count")
    if not isinstance(scoped_count, int) or scoped_count <= 0:
        issues.append("policy_scoped_queued_count must be positive")
    for name in (
        "command_plan_ready_count",
        "command_built_count",
        "handler_executed_count",
        "frames_written_count",
        "readback_count",
    ):
        if top_level_counts.get(name) != scoped_count:
            issues.append(f"{name} must equal policy_scoped_queued_count")
    if artifact_counts.get("policy_scoped_queue_items") != scoped_count:
        issues.append("policy_scoped_queue_items must equal policy_scoped_queued_count")

    if issues:
        return _rejected_registry_report(
            acceptance_path=acceptance_file,
            output_path=Path(output_path),
            issues=issues,
        )

    entry = _build_registry_entry(acceptance_file, acceptance)
    registry_path = Path(output_path)
    _write_registry_entry(registry_path, entry, append=append)

    return {
        "schema": ISOLATED_ROUTE_PIPELINE_BASELINE_REGISTRY_SCHEMA,
        "acceptance_path": str(acceptance_file),
        "output_path": str(registry_path),
        "append": append,
        "registered_count": 1,
        "accepted_baseline": entry["accepted_baseline"],
        "baseline_ref": entry["baseline_ref"],
        "entry_digest": entry["entry_digest"],
        "issues": [],
        "registry_success": True,
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


def _build_registry_entry(acceptance_file: Path, acceptance: Mapping[str, Any]) -> dict[str, Any]:
    top_level_counts = dict(acceptance.get("top_level_counts", {}))
    artifact_counts = dict(acceptance.get("artifact_counts", {}))
    raw_entry = {
        "schema": ISOLATED_ROUTE_PIPELINE_BASELINE_REGISTRY_ENTRY_SCHEMA,
        "accepted_baseline": acceptance.get("accepted_baseline"),
        "acceptance_schema": acceptance.get("schema"),
        "acceptance_path": str(acceptance_file),
        "pipeline_report_path": acceptance.get("pipeline_report_path"),
        "pipeline_schema": acceptance.get("pipeline_schema"),
        "policy_decision_id": acceptance.get("policy_decision_id"),
        "runtime_root": acceptance.get("runtime_root"),
        "isolated_runtime_root": acceptance.get("isolated_runtime_root"),
        "top_level_counts": top_level_counts,
        "artifact_counts": artifact_counts,
        "safety_flags": {
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
        },
    }
    digest_payload = json.dumps(raw_entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(digest_payload).hexdigest()
    entry = dict(raw_entry)
    entry["entry_digest"] = digest
    entry["baseline_ref"] = f"baseline:{acceptance.get('accepted_baseline')}:{digest[:16]}"
    return entry


def _write_registry_entry(path: Path, entry: Mapping[str, Any], *, append: bool) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise IsolatedRoutePipelineBaselineRegistryError(
            "output filename must be isolated_route_pipeline_baseline_registry.jsonl"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(json.dumps(dict(entry), sort_keys=True, separators=(",", ":")) + "\n")


def _rejected_registry_report(
    *,
    acceptance_path: Path,
    output_path: Path,
    issues: list[str],
) -> dict[str, Any]:
    return {
        "schema": ISOLATED_ROUTE_PIPELINE_BASELINE_REGISTRY_SCHEMA,
        "acceptance_path": str(acceptance_path),
        "output_path": str(output_path),
        "append": False,
        "registered_count": 0,
        "accepted_baseline": None,
        "baseline_ref": None,
        "entry_digest": None,
        "issues": issues,
        "registry_success": False,
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


def _assert_false_flags(acceptance: Mapping[str, Any], issues: list[str]) -> None:
    for flag in (
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
    ):
        if acceptance.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise IsolatedRoutePipelineBaselineRegistryError("acceptance must be a JSON object")
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register accepted isolated route pipeline baseline.")
    parser.add_argument("--acceptance", required=True, help="Path to isolated_route_pipeline_acceptance.json.")
    parser.add_argument("--output", required=True, help="Path to isolated_route_pipeline_baseline_registry.jsonl.")
    parser.add_argument("--append", action="store_true", help="Append instead of replacing the registry.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = register_isolated_route_pipeline_baseline(
        acceptance_path=Path(args.acceptance),
        output_path=Path(args.output),
        append=args.append,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"registry_success: {report['registry_success']}")
        print(f"registered_count: {report['registered_count']}")
        print(f"accepted_baseline: {report['accepted_baseline']}")
        print(f"baseline_ref: {report['baseline_ref']}")
        print(f"issues: {len(report['issues'])}")
    return 0 if report["registry_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
