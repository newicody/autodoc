#!/usr/bin/env python3
"""Accept controlled SQL/Qdrant projection contract from the 0211 plan.

0212 is the Bloc F controlled SQL/Qdrant projection acceptance patch.

It reads sql_qdrant_projection_plan.json from 0211 and writes
controlled_sql_qdrant_projection_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0212 must reuse the 0211 SQL/Qdrant projection plan and audited existing surfaces.

0212 explicitly unlocks controlled SQL/Qdrant projection acceptance for this
phase only.

0212 does not write SQL rows.
0212 does not write Qdrant points.
0212 does not add a new SQL backend.
0212 does not add a new Qdrant backend.
0212 does not rewrite runtime history.
0212 does not execute Scheduler.run.
0212 does not modify Scheduler.run.
0212 does not import runtime handler modules.
0212 does not call handle_scheduler_route_command.
0212 does not call handle_scheduler_route_request.
0212 does not call prepare_route_proxy_runtime.
0212 does not call read_route_frame.
0212 does not request writer permits.
0212 does not call write_route_frame.
0212 does not write ControlProxy or RouteProxy frames.
0212 does not call GitHub API or use network.

SQL remains durable authority.
Qdrant remains projection/search/recall only.
Qdrant payloads must carry sql_ref.
Qdrant recall must rehydrate from SQL.
0212 closes Bloc F by writing controlled_sql_qdrant_projection_acceptance.json only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


CONTROLLED_SQL_QDRANT_PROJECTION_ACCEPTANCE_SCHEMA = (
    "missipy.sql_qdrant.controlled_projection_acceptance.v1"
)
EXPECTED_PLAN_SCHEMA = "missipy.sql_qdrant.projection_plan.v1"
DEFAULT_OUTPUT_NAME = "controlled_sql_qdrant_projection_acceptance.json"

FALSE_PLAN_FLAGS = (
    "execution_allowed_by_0211",
    "sql_write_allowed_by_0211",
    "qdrant_write_allowed_by_0211",
    "projection_write_allowed_by_0211",
    "runtime_imports_executed_by_0211",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0211",
    "routeproxy_prepared_by_0211",
    "read_route_frame_called_by_0211",
    "writer_permits_requested_by_0211",
    "frames_written_by_0211",
    "controlproxy_frames_written_by_0211",
    "eventbus_instantiated_by_0211",
    "network_used_by_0211",
    "sql_written_by_0211",
    "qdrant_written_by_0211",
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


class ControlledSqlQdrantProjectionAcceptanceError(ValueError):
    """Raised when controlled SQL/Qdrant projection acceptance is unsafe."""


def accept_controlled_sql_qdrant_projection(
    *,
    projection_plan_path: Path | str,
    repo_root: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Accept controlled SQL/Qdrant projection contract without backend writes."""

    plan_path = Path(projection_plan_path)
    root = Path(repo_root)
    plan = _read_json_file(plan_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_plan(plan, issues, warnings)

    if not root.exists():
        issues.append("repo_root must exist")
    if not root.is_dir():
        issues.append("repo_root must be a directory")

    target_runtime_root = Path(str(plan.get("target_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be controlled_sql_qdrant_projection_acceptance.json")
    if target_runtime_root.is_absolute() and final_output.is_absolute():
        if not _is_within_or_equal(final_output, target_runtime_root):
            issues.append("controlled projection acceptance output must be inside target_runtime_root")

    selected_surfaces = _selected_surfaces(plan)
    _audit_selected_surfaces(root, selected_surfaces, issues)

    sql_ref = str(plan.get("source_baseline_ref", ""))
    source_entry_digest = str(plan.get("source_entry_digest", ""))
    repair_digest = str(plan.get("repair_digest", ""))
    if not sql_ref:
        issues.append("sql_ref/source_baseline_ref must be present")
    if not source_entry_digest:
        issues.append("source_entry_digest must be present")
    if not repair_digest:
        issues.append("repair_digest must be present")

    qdrant_payload = {
        "sql_ref": sql_ref,
        "source_entry_digest": source_entry_digest,
        "repair_digest": repair_digest,
    }
    projection_record = {
        "projection_strategy": plan.get("projection_strategy"),
        "sql_ref": sql_ref,
        "qdrant_payload": qdrant_payload,
        "sql_authority_surface": plan.get("sql_authority_surface"),
        "qdrant_projection_surface": plan.get("qdrant_projection_surface"),
        "rehydrate_surface": plan.get("rehydrate_surface"),
        "provenance_surface": plan.get("provenance_surface"),
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "qdrant_role": "projection/search/recall only",
        "sql_role": "durable authority",
        "rehydration_contract": "hydrate returned sql_ref from SQL authority",
    }
    projection_digest = _stable_digest(projection_record)

    accepted = not issues
    acceptance = {
        "schema": CONTROLLED_SQL_QDRANT_PROJECTION_ACCEPTANCE_SCHEMA,
        "bloc": "F",
        "bloc_name": "sql-qdrant-projection-readiness",
        "projection_plan_path": str(plan_path),
        "projection_plan_schema": plan.get("schema"),
        "target_runtime_root": plan.get("target_runtime_root"),
        "target_isolated_runtime_root": plan.get("target_isolated_runtime_root"),
        "accepted_baseline": "controlled-sql-qdrant-projection-contract-v1",
        "controlled_sql_qdrant_projection_accepted": accepted,
        "controlled_sql_qdrant_projection_executed": True,
        "sql_qdrant_projection_contract_accepted": accepted,
        "bloc_f_complete": accepted,
        "phase_re_evaluated": True,
        "next_bloc": "G",
        "next_bloc_name": "context-recall-integration",
        "next_recommended_patch": "0213-context_recall_integration_audit",
        "execution_unlocked_by_0212": True,
        "execution_allowed_by_0212": True,
        "sql_write_allowed_by_0212": False,
        "qdrant_write_allowed_by_0212": False,
        "sql_written_by_0212": False,
        "qdrant_written_by_0212": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "projection_strategy": plan.get("projection_strategy"),
        "projection_record": projection_record,
        "projection_digest": projection_digest,
        "sql_ref": sql_ref,
        "qdrant_payload": qdrant_payload,
        "payload_contains_sql_ref": "sql_ref" in qdrant_payload and bool(qdrant_payload["sql_ref"]),
        "rehydration_required": True,
        "selected_surfaces": selected_surfaces,
        "projection_contract": plan.get("projection_contract"),
        "source_baseline_ref": sql_ref,
        "source_entry_digest": source_entry_digest,
        "repair_digest": repair_digest,
        "issues": issues,
        "warnings": warnings,
        "existing_surfaces_reused": True,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_scheduler_added": False,
        "new_controlproxy_runtime_added": False,
        "new_routeproxy_runtime_added": False,
        "new_github_client_added": False,
        "new_graph_renderer_added": False,
        "new_inference_path_added": False,
        "runtime_imports_executed_by_0212": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0212": False,
        "routeproxy_prepared_by_0212": False,
        "read_route_frame_called_by_0212": False,
        "writer_permits_requested_by_0212": False,
        "frames_written_by_0212": False,
        "controlproxy_frames_written_by_0212": False,
        "eventbus_instantiated_by_0212": False,
        "network_used_by_0212": False,
        "runtime_history_rewritten_by_0212": False,
    }

    _write_acceptance(final_output, acceptance)
    return acceptance


def _audit_plan(plan: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if plan.get("schema") != EXPECTED_PLAN_SCHEMA:
        issues.append("SQL/Qdrant projection plan schema mismatch")
    if plan.get("sql_qdrant_projection_plan_ready") is not True:
        issues.append("sql_qdrant_projection_plan_ready must be true")
    if plan.get("projection_strategy") != "sql_authority_qdrant_projection_sql_ref_rehydrate":
        issues.append("projection_strategy must be sql_authority_qdrant_projection_sql_ref_rehydrate")
    if plan.get("p0212_may_execute_controlled_projection_acceptance") is not True:
        issues.append("p0212_may_execute_controlled_projection_acceptance must be true")
    if plan.get("planned_next_patch") != "0212-controlled_sql_qdrant_projection_acceptance":
        issues.append("planned_next_patch must be 0212-controlled_sql_qdrant_projection_acceptance")
    if plan.get("issues") not in ([], None):
        issues.append("SQL/Qdrant projection plan issues must be empty")
    if isinstance(plan.get("warnings"), list) and plan.get("warnings"):
        warnings.extend(str(item) for item in plan.get("warnings", []))
    contract = plan.get("projection_contract")
    if not isinstance(contract, Mapping):
        issues.append("projection_contract must be present")
    else:
        if contract.get("sql_role") != "durable authority":
            issues.append("projection_contract sql_role must be durable authority")
        if contract.get("qdrant_role") != "projection/search/recall only":
            issues.append("projection_contract qdrant_role must be projection/search/recall only")
        if contract.get("payload_contract") != "Qdrant payloads carry sql_ref":
            issues.append("projection_contract payload_contract must require sql_ref")
        if contract.get("rehydration_contract") != "hydrate returned sql_ref from SQL authority":
            issues.append("projection_contract rehydration_contract must require SQL rehydrate")
    if plan.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for flag in FALSE_PLAN_FLAGS:
        if plan.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if plan.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _selected_surfaces(plan: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "sql_authority_surface": _surface_mapping(plan.get("sql_authority_surface")),
        "qdrant_projection_surface": _surface_mapping(plan.get("qdrant_projection_surface")),
        "rehydrate_surface": _surface_mapping(plan.get("rehydrate_surface")),
        "provenance_surface": _surface_mapping(plan.get("provenance_surface")),
    }


def _surface_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    tokens = value.get("matched_tokens")
    return {
        "path": str(value.get("path", "")),
        "matched_tokens": [str(token) for token in tokens] if isinstance(tokens, list) else [],
        "use_before_new_code": bool(value.get("use_before_new_code")),
    }


def _audit_selected_surfaces(root: Path, selected_surfaces: Mapping[str, Mapping[str, Any]], issues: list[str]) -> None:
    for name, surface in selected_surfaces.items():
        path = surface.get("path")
        if not isinstance(path, str) or not path:
            issues.append(f"{name} path must be present")
            continue
        if Path(path).is_absolute():
            issues.append(f"{name} path must be repository-relative")
            continue
        if ".." in Path(path).parts:
            issues.append(f"{name} path must not escape repo root")
            continue
        if not (root / path).exists():
            issues.append(f"{name} path must exist: {path}")
        if surface.get("use_before_new_code") is not True:
            issues.append(f"{name} must be marked use_before_new_code")


def _stable_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ControlledSqlQdrantProjectionAcceptanceError("input must be a JSON object")
    return raw


def _write_acceptance(path: Path, acceptance: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ControlledSqlQdrantProjectionAcceptanceError(
            "output filename must be controlled_sql_qdrant_projection_acceptance.json"
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
    parser = argparse.ArgumentParser(description="Accept controlled SQL/Qdrant projection contract.")
    parser.add_argument("--projection-plan", required=True, help="Path to sql_qdrant_projection_plan.json.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--output", help="Optional controlled_sql_qdrant_projection_acceptance.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    acceptance = accept_controlled_sql_qdrant_projection(
        projection_plan_path=Path(args.projection_plan),
        repo_root=Path(args.repo_root),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(acceptance, indent=2, sort_keys=True))
    else:
        print(f"controlled_sql_qdrant_projection_accepted: {acceptance['controlled_sql_qdrant_projection_accepted']}")
        print(f"bloc_f_complete: {acceptance['bloc_f_complete']}")
        print(f"sql_ref: {acceptance['sql_ref']}")
        print(f"payload_contains_sql_ref: {acceptance['payload_contains_sql_ref']}")
        print(f"sql_written_by_0212: {acceptance['sql_written_by_0212']}")
        print(f"qdrant_written_by_0212: {acceptance['qdrant_written_by_0212']}")
        print(f"next_bloc: {acceptance['next_bloc']}")
        print(f"issues: {len(acceptance['issues'])}")
    return 0 if acceptance["controlled_sql_qdrant_projection_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
