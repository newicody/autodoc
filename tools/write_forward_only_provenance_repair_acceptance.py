#!/usr/bin/env python3
"""Write and accept forward-only provenance repair from the 0208 plan.

0209 is the Bloc E forward-only provenance repair acceptance patch.

It reads provenance_repair_plan.json from 0208 and writes
provenance_repair_acceptance.json only.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0209 must write a forward-only provenance repair artifact without rewriting
historical runtime artifacts.

0209 repairs source_baseline_ref by forward-only acceptance artifact.
0209 repairs source_entry_digest by forward-only acceptance artifact.
0209 does not rewrite controlled_dev_routeproxy_smoke_post_execution_acceptance.json.
0209 does not rewrite runtime history.
0209 does not write SQL.
0209 does not write Qdrant.
0209 does not execute Scheduler.run.
0209 does not modify Scheduler.run.
0209 does not import runtime handler modules.
0209 does not call handle_scheduler_route_command.
0209 does not call handle_scheduler_route_request.
0209 does not call prepare_route_proxy_runtime.
0209 does not call mark_route_frame_stale.
0209 does not call read_route_frame.
0209 does not request writer permits.
0209 does not call write_route_frame.
0209 does not write ControlProxy or RouteProxy frames.
0209 does not call GitHub API or use network.

0209 closes Bloc E only by writing provenance_repair_acceptance.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


FORWARD_ONLY_PROVENANCE_REPAIR_ACCEPTANCE_SCHEMA = (
    "missipy.provenance.forward_only_repair_acceptance.v1"
)
EXPECTED_PLAN_SCHEMA = "missipy.provenance.repair_plan.v1"
DEFAULT_OUTPUT_NAME = "provenance_repair_acceptance.json"
SOURCE_ARTIFACT = "controlled_dev_routeproxy_smoke_post_execution_acceptance.json"
REGISTRY_ARTIFACT = "controlled_dev_routeproxy_smoke_registry.jsonl"

FALSE_PLAN_FLAGS = (
    "runtime_history_rewrite_allowed_by_0208",
    "execution_allowed_by_0208",
    "sql_write_allowed_by_0208",
    "qdrant_write_allowed_by_0208",
    "provenance_repair_write_allowed_by_0208",
    "runtime_imports_executed_by_0208",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0208",
    "routeproxy_prepared_by_0208",
    "mark_route_frame_stale_called_by_0208",
    "read_route_frame_called_by_0208",
    "writer_permits_requested_by_0208",
    "frames_written_by_0208",
    "controlproxy_frames_written_by_0208",
    "eventbus_instantiated_by_0208",
    "network_used_by_0208",
    "sql_written_by_0208",
    "qdrant_written_by_0208",
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


class ForwardOnlyProvenanceRepairAcceptanceError(ValueError):
    """Raised when forward-only provenance repair acceptance is unsafe."""


def write_forward_only_provenance_repair_acceptance(
    *,
    provenance_repair_plan_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Write a forward-only provenance repair acceptance artifact."""

    plan_path = Path(provenance_repair_plan_path)
    plan = _read_json_file(plan_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_plan(plan, issues, warnings)

    target_runtime_root = Path(str(plan.get("target_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be provenance_repair_acceptance.json")
    if target_runtime_root.is_absolute() and final_output.is_absolute():
        if not _is_within_or_equal(final_output, target_runtime_root):
            issues.append("provenance repair acceptance output must be inside target_runtime_root")

    source_artifact_path = target_runtime_root / SOURCE_ARTIFACT
    registry_artifact_path = target_runtime_root / REGISTRY_ARTIFACT
    source_artifact = _read_optional_json_file(source_artifact_path)
    registry_entries = _read_optional_jsonl_file(registry_artifact_path)

    planned_source_baseline_ref = str(plan.get("planned_source_baseline_ref", ""))
    planned_source_entry_digest = str(plan.get("planned_source_entry_digest", ""))
    planned_registry_entry_ref = str(plan.get("planned_registry_entry_ref", ""))

    _audit_source_artifact(
        source_artifact=source_artifact,
        planned_source_baseline_ref=planned_source_baseline_ref,
        issues=issues,
    )
    _audit_registry_artifact(
        registry_entries=registry_entries,
        planned_source_entry_digest=planned_source_entry_digest,
        planned_registry_entry_ref=planned_registry_entry_ref,
        issues=issues,
    )

    repair_record = _build_repair_record(
        plan=plan,
        planned_source_baseline_ref=planned_source_baseline_ref,
        planned_source_entry_digest=planned_source_entry_digest,
        planned_registry_entry_ref=planned_registry_entry_ref,
        source_artifact_path=source_artifact_path,
        registry_artifact_path=registry_artifact_path,
    )
    repair_digest = _stable_digest(repair_record)

    accepted = not issues
    acceptance = {
        "schema": FORWARD_ONLY_PROVENANCE_REPAIR_ACCEPTANCE_SCHEMA,
        "bloc": "E",
        "bloc_name": "sql-qdrant-provenance-repair",
        "provenance_repair_plan_path": str(plan_path),
        "provenance_repair_plan_schema": plan.get("schema"),
        "target_runtime_root": plan.get("target_runtime_root"),
        "target_isolated_runtime_root": plan.get("target_isolated_runtime_root"),
        "accepted_baseline": "forward-only-provenance-repair-v1",
        "source_artifact": SOURCE_ARTIFACT,
        "registry_artifact": REGISTRY_ARTIFACT,
        "repair_strategy": "forward_only_artifact",
        "forward_only_provenance_repair_written": accepted,
        "forward_only_provenance_repair_accepted": accepted,
        "provenance_repair_accepted": accepted,
        "bloc_e_complete": accepted,
        "phase_re_evaluated": True,
        "next_bloc": "F",
        "next_bloc_name": "sql-qdrant-projection-readiness",
        "next_recommended_patch": "0210-sql_qdrant_projection_readiness_audit",
        "repaired_fields": [
            "source_baseline_ref",
            "source_entry_digest",
        ],
        "source_baseline_ref": planned_source_baseline_ref,
        "source_baseline_ref_source": plan.get("planned_source_baseline_ref_source"),
        "source_entry_digest": planned_source_entry_digest,
        "source_entry_digest_source": plan.get("planned_source_entry_digest_source"),
        "registry_entry_ref": planned_registry_entry_ref,
        "repair_record": repair_record,
        "repair_digest": repair_digest,
        "rewrite_runtime_history_allowed_by_0209": False,
        "runtime_history_rewritten_by_0209": False,
        "source_artifact_rewritten_by_0209": False,
        "sql_write_allowed_by_0209": False,
        "qdrant_write_allowed_by_0209": False,
        "sql_written_by_0209": False,
        "qdrant_written_by_0209": False,
        "execution_allowed_by_0209": True,
        "provenance_repair_write_allowed_by_0209": True,
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
        "runtime_imports_executed_by_0209": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0209": False,
        "routeproxy_prepared_by_0209": False,
        "mark_route_frame_stale_called_by_0209": False,
        "read_route_frame_called_by_0209": False,
        "writer_permits_requested_by_0209": False,
        "frames_written_by_0209": False,
        "controlproxy_frames_written_by_0209": False,
        "eventbus_instantiated_by_0209": False,
        "network_used_by_0209": False,
    }

    _write_acceptance(final_output, acceptance)
    return acceptance


def _audit_plan(plan: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if plan.get("schema") != EXPECTED_PLAN_SCHEMA:
        issues.append("provenance repair plan schema mismatch")
    if plan.get("provenance_repair_plan_ready") is not True:
        issues.append("provenance_repair_plan_ready must be true")
    if plan.get("repair_strategy") != "forward_only_artifact":
        issues.append("repair_strategy must be forward_only_artifact")
    if plan.get("planned_output") != DEFAULT_OUTPUT_NAME:
        issues.append("planned_output must be provenance_repair_acceptance.json")
    if plan.get("planned_next_patch") != "0209-forward_only_provenance_repair_acceptance":
        issues.append("planned_next_patch must be 0209-forward_only_provenance_repair_acceptance")
    if plan.get("p0209_may_write_forward_only_provenance_repair") is not True:
        issues.append("p0209_may_write_forward_only_provenance_repair must be true")
    if plan.get("issues") not in ([], None):
        issues.append("provenance repair plan issues must be empty")
    if isinstance(plan.get("warnings"), list) and plan.get("warnings"):
        warnings.extend(str(item) for item in plan.get("warnings", []))
    if not isinstance(plan.get("planned_source_baseline_ref"), str) or not plan.get("planned_source_baseline_ref"):
        issues.append("planned_source_baseline_ref must be present")
    if not isinstance(plan.get("planned_source_entry_digest"), str) or not plan.get("planned_source_entry_digest"):
        issues.append("planned_source_entry_digest must be present")
    if not isinstance(plan.get("planned_registry_entry_ref"), str) or not plan.get("planned_registry_entry_ref"):
        issues.append("planned_registry_entry_ref must be present")
    for flag in FALSE_PLAN_FLAGS:
        if plan.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if plan.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _audit_source_artifact(
    *,
    source_artifact: Mapping[str, Any] | None,
    planned_source_baseline_ref: str,
    issues: list[str],
) -> None:
    if source_artifact is None:
        issues.append(f"{SOURCE_ARTIFACT} must exist")
        return
    observed = source_artifact.get("controlled_dev_baseline_ref")
    if observed != planned_source_baseline_ref:
        issues.append("planned_source_baseline_ref must match source artifact controlled_dev_baseline_ref")
    if source_artifact.get("source_baseline_ref") not in ("", None):
        issues.append("source artifact source_baseline_ref is already populated; do not rewrite")
    if source_artifact.get("source_entry_digest") not in ("", None):
        issues.append("source artifact source_entry_digest is already populated; do not rewrite")


def _audit_registry_artifact(
    *,
    registry_entries: list[Mapping[str, Any]],
    planned_source_entry_digest: str,
    planned_registry_entry_ref: str,
    issues: list[str],
) -> None:
    if not registry_entries:
        issues.append(f"{REGISTRY_ARTIFACT} must contain at least one entry")
        return
    match = None
    for entry in registry_entries:
        if entry.get("entry_digest") == planned_source_entry_digest:
            match = entry
            break
    if match is None:
        issues.append("planned_source_entry_digest must exist in registry artifact")
        return
    if planned_registry_entry_ref and match.get("entry_ref") != planned_registry_entry_ref:
        issues.append("planned_registry_entry_ref must match registry artifact entry_ref")


def _build_repair_record(
    *,
    plan: Mapping[str, Any],
    planned_source_baseline_ref: str,
    planned_source_entry_digest: str,
    planned_registry_entry_ref: str,
    source_artifact_path: Path,
    registry_artifact_path: Path,
) -> dict[str, Any]:
    return {
        "repair_strategy": "forward_only_artifact",
        "source_artifact": SOURCE_ARTIFACT,
        "source_artifact_path": str(source_artifact_path),
        "registry_artifact": REGISTRY_ARTIFACT,
        "registry_artifact_path": str(registry_artifact_path),
        "source_baseline_ref": planned_source_baseline_ref,
        "source_baseline_ref_source": plan.get("planned_source_baseline_ref_source"),
        "source_entry_digest": planned_source_entry_digest,
        "source_entry_digest_source": plan.get("planned_source_entry_digest_source"),
        "registry_entry_ref": planned_registry_entry_ref,
        "runtime_history_rewrite_allowed": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
    }


def _stable_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_optional_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _read_json_file(path)


def _read_optional_jsonl_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        if isinstance(raw, dict):
            rows.append(raw)
    return rows


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ForwardOnlyProvenanceRepairAcceptanceError("input must be a JSON object")
    return raw


def _write_acceptance(path: Path, acceptance: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ForwardOnlyProvenanceRepairAcceptanceError(
            "output filename must be provenance_repair_acceptance.json"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(acceptance, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_within_or_equal(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write forward-only provenance repair acceptance.")
    parser.add_argument("--provenance-repair-plan", required=True, help="Path to provenance_repair_plan.json.")
    parser.add_argument("--output", help="Optional provenance_repair_acceptance.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    acceptance = write_forward_only_provenance_repair_acceptance(
        provenance_repair_plan_path=Path(args.provenance_repair_plan),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(acceptance, indent=2, sort_keys=True))
    else:
        print(f"forward_only_provenance_repair_accepted: {acceptance['forward_only_provenance_repair_accepted']}")
        print(f"provenance_repair_accepted: {acceptance['provenance_repair_accepted']}")
        print(f"bloc_e_complete: {acceptance['bloc_e_complete']}")
        print(f"source_baseline_ref: {acceptance['source_baseline_ref']}")
        print(f"source_entry_digest: {acceptance['source_entry_digest']}")
        print(f"next_bloc: {acceptance['next_bloc']}")
        print(f"issues: {len(acceptance['issues'])}")
    return 0 if acceptance["forward_only_provenance_repair_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
