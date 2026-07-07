#!/usr/bin/env python3
"""Record Bloc A coherence for the route pipeline plan.

0197 is the Bloc A coherence record only.

It reads isolated_route_pipeline_promotion_readiness_acceptance.json from 0196
and writes route_pipeline_bloc_a_coherence_record.json. It closes Bloc A,
records phase re-evaluation, and opens the next Bloc B direction.

It must reuse the existing 0196 readiness acceptance artifact. It must not
introduce a new runtime handler, adapter, bus, RouteProxy runtime, ControlProxy
runtime, SQL backend, Qdrant backend, GitHub client, graph renderer, or
inference path.

Important: Execution locks are not permanent. Bloc A keeps execution disabled
because Bloc A is a plan/audit/readiness bloc. A later execution bloc may unlock execution explicitly
when the phase requires it, with policy_decision_id, gate, documentation, audit,
and acceptance.

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


ROUTE_PIPELINE_BLOC_A_COHERENCE_SCHEMA = "missipy.route_pipeline.bloc_a_coherence_record.v1"
EXPECTED_READINESS_SCHEMA = "missipy.route_pipeline.isolated_promotion_readiness_acceptance.v1"
EXPECTED_BASELINE = "isolated-route-pipeline-write-read-v1"
EXPECTED_PROMOTION_TARGET = "controlled-dev-routeproxy-smoke"
DEFAULT_OUTPUT_NAME = "route_pipeline_bloc_a_coherence_record.json"

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


class RoutePipelineBlocACoherenceError(ValueError):
    """Raised when Bloc A coherence cannot be recorded safely."""


def record_route_pipeline_bloc_a_coherence(
    *,
    readiness_acceptance_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Record Bloc A coherence from a clean 0196 readiness acceptance."""

    path = Path(readiness_acceptance_path)
    readiness = _read_json_file(path)
    issues: list[str] = []
    warnings: list[str] = []

    if readiness.get("schema") != EXPECTED_READINESS_SCHEMA:
        issues.append("readiness acceptance schema mismatch")
    if readiness.get("promotion_readiness_accepted") is not True:
        issues.append("promotion_readiness_accepted must be true")
    if readiness.get("controlled_dev_smoke_ready") is not True:
        issues.append("controlled_dev_smoke_ready must be true")
    if readiness.get("execution_allowed_by_0196") is not False:
        issues.append("execution_allowed_by_0196 must remain false")
    if readiness.get("phase_re_evaluation_required_before_execution") is not True:
        issues.append("phase_re_evaluation_required_before_execution must be true")
    if readiness.get("accepted_baseline") != EXPECTED_BASELINE:
        issues.append("accepted_baseline mismatch")
    if readiness.get("promotion_target") != EXPECTED_PROMOTION_TARGET:
        issues.append("promotion_target mismatch")
    if readiness.get("next_required_patch") != "0197-bloc_a_coherence_record":
        issues.append("next_required_patch must be 0197-bloc_a_coherence_record")
    if readiness.get("issues") not in ([], None):
        issues.append("readiness issues must be empty")
    if isinstance(readiness.get("warnings"), list) and readiness.get("warnings"):
        warnings.extend(str(item) for item in readiness.get("warnings", []))
    if readiness.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")

    _audit_required_paths(readiness, issues)
    _audit_false_flags(readiness, FALSE_SAFETY_FLAGS, issues)
    _audit_false_flags(readiness, FALSE_NEW_SURFACE_FLAGS, issues)

    record = {
        "schema": ROUTE_PIPELINE_BLOC_A_COHERENCE_SCHEMA,
        "bloc": "A",
        "bloc_name": "isolated-prototype-stabilization",
        "bloc_patch_limit": 3,
        "bloc_patches": [
            "0195-isolated_route_pipeline_promotion_plan_audit",
            "0196-isolated_route_pipeline_promotion_readiness_acceptance",
            "0197-bloc_a_coherence_record",
        ],
        "readiness_acceptance_path": str(path),
        "readiness_acceptance_schema": readiness.get("schema"),
        "selected_baseline_ref": readiness.get("selected_baseline_ref"),
        "selected_entry_digest": readiness.get("selected_entry_digest"),
        "accepted_baseline": readiness.get("accepted_baseline"),
        "source_policy_decision_id": readiness.get("source_policy_decision_id"),
        "source_runtime_root": readiness.get("source_runtime_root"),
        "source_isolated_runtime_root": readiness.get("source_isolated_runtime_root"),
        "target_runtime_root": readiness.get("target_runtime_root"),
        "target_isolated_runtime_root": readiness.get("target_isolated_runtime_root"),
        "promotion_target": readiness.get("promotion_target"),
        "bloc_a_coherence_accepted": not issues,
        "bloc_a_complete": not issues,
        "phase_re_evaluated": True,
        "plan_adjustment_required": False,
        "rules_adjustment_required": False,
        "next_bloc": "B",
        "next_bloc_name": "controlled-dev-smoke",
        "next_recommended_patch": "0198-controlled_dev_smoke_plan",
        "execution_allowed_by_0197": False,
        "future_execution_can_be_unlocked": True,
        "future_execution_unlock_requires": [
            "explicit execution patch in an execution bloc",
            "explicit policy_decision_id",
            "reuse or adapt existing pipeline tools before adding code",
            "doc/code-rules/code_rule.md applied",
            "docs, graph, changelog, manifest, and rule updated",
            "post-execution artifact audit",
            "post-audit acceptance gate",
        ],
        "coherence_decisions": [
            "Bloc A remains a preparation bloc and does not execute controlled-dev-routeproxy-smoke.",
            "Execution locks are phase gates, not permanent prohibitions.",
            "Bloc B may prepare and then explicitly unlock controlled dev execution if its gate requires it.",
            "Existing surfaces must be reused or adapted before adding new runtime surfaces.",
            "Every bloc must end with re-evaluation and coherence before moving forward.",
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
        _write_record(Path(output_path), record)

    return record


def _audit_required_paths(readiness: Mapping[str, Any], issues: list[str]) -> None:
    for key in (
        "promotion_plan_audit_path",
        "source_runtime_root",
        "source_isolated_runtime_root",
        "target_runtime_root",
        "target_isolated_runtime_root",
    ):
        if not isinstance(readiness.get(key), str) or not readiness.get(key):
            issues.append(f"{key} must be present")

    target_runtime_root = readiness.get("target_runtime_root")
    target_isolated_runtime_root = readiness.get("target_isolated_runtime_root")
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


def _audit_false_flags(readiness: Mapping[str, Any], flags: tuple[str, ...], issues: list[str]) -> None:
    for flag in flags:
        if readiness.get(flag) is not False:
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
        raise RoutePipelineBlocACoherenceError("readiness acceptance must be a JSON object")
    return raw


def _write_record(path: Path, record: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise RoutePipelineBlocACoherenceError("output filename must be route_pipeline_bloc_a_coherence_record.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record Route pipeline Bloc A coherence.")
    parser.add_argument(
        "--readiness-acceptance",
        required=True,
        help="Path to isolated_route_pipeline_promotion_readiness_acceptance.json.",
    )
    parser.add_argument("--output", help="Optional route_pipeline_bloc_a_coherence_record.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    record = record_route_pipeline_bloc_a_coherence(
        readiness_acceptance_path=Path(args.readiness_acceptance),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(record, indent=2, sort_keys=True))
    else:
        print(f"bloc_a_coherence_accepted: {record['bloc_a_coherence_accepted']}")
        print(f"bloc_a_complete: {record['bloc_a_complete']}")
        print(f"next_bloc: {record['next_bloc']}")
        print(f"future_execution_can_be_unlocked: {record['future_execution_can_be_unlocked']}")
        print(f"execution_allowed_by_0197: {record['execution_allowed_by_0197']}")
        print(f"issues: {len(record['issues'])}")
    return 0 if record["bloc_a_coherence_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
