#!/usr/bin/env python3
"""Plan SQL/Qdrant projection from the 0210 readiness audit.

0211 is the Bloc F SQL/Qdrant projection plan only.

It reads sql_qdrant_projection_readiness_audit.json from 0210 and writes
sql_qdrant_projection_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0211 must reuse the 0210 readiness audit before any SQL/Qdrant projection write
is allowed.

0211 does not write SQL.
0211 does not write Qdrant.
0211 does not add a new SQL backend.
0211 does not add a new Qdrant backend.
0211 does not rewrite runtime history.
0211 does not execute Scheduler.run.
0211 does not modify Scheduler.run.
0211 does not import runtime handler modules.
0211 does not call handle_scheduler_route_command.
0211 does not call handle_scheduler_route_request.
0211 does not call prepare_route_proxy_runtime.
0211 does not call read_route_frame.
0211 does not request writer permits.
0211 does not call write_route_frame.
0211 does not write ControlProxy or RouteProxy frames.
0211 does not call GitHub API or use network.

SQL remains durable authority.
Qdrant remains projection/search/recall only.
Qdrant payloads must carry sql_ref.
Qdrant recall must rehydrate from SQL.
0211 plans projection only; P0212 may execute controlled projection acceptance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


SQL_QDRANT_PROJECTION_PLAN_SCHEMA = "missipy.sql_qdrant.projection_plan.v1"
EXPECTED_AUDIT_SCHEMA = "missipy.sql_qdrant.projection_readiness_audit.v1"
DEFAULT_OUTPUT_NAME = "sql_qdrant_projection_plan.json"

FALSE_AUDIT_FLAGS = (
    "runtime_imports_executed_by_0210",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0210",
    "routeproxy_prepared_by_0210",
    "read_route_frame_called_by_0210",
    "writer_permits_requested_by_0210",
    "frames_written_by_0210",
    "controlproxy_frames_written_by_0210",
    "eventbus_instantiated_by_0210",
    "network_used_by_0210",
    "sql_write_allowed_by_0210",
    "qdrant_write_allowed_by_0210",
    "sql_written_by_0210",
    "qdrant_written_by_0210",
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


class SqlQdrantProjectionPlanError(ValueError):
    """Raised when SQL/Qdrant projection planning is unsafe."""


def plan_sql_qdrant_projection(
    *,
    readiness_audit_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Plan SQL/Qdrant projection without SQL/Qdrant writes."""

    audit_path = Path(readiness_audit_path)
    audit = _read_json_file(audit_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_readiness(audit, issues, warnings)

    target_runtime_root = Path(str(audit.get("target_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be sql_qdrant_projection_plan.json")

    sql_surface = _select_surface(audit.get("sql_surfaces"), required_token="sql_ref")
    if not sql_surface:
        sql_surface = _select_surface(audit.get("sql_surfaces"), required_token="DbApiSqlContextStore")
    qdrant_surface = _select_surface(audit.get("qdrant_surfaces"), required_token="Qdrant")
    if not qdrant_surface:
        qdrant_surface = _select_surface(audit.get("qdrant_surfaces"), required_token="qdrant")
    rehydrate_surface = _select_surface(audit.get("rehydrate_surfaces"), required_token="sql_ref")
    provenance_surface = _select_surface(audit.get("provenance_surfaces"), required_token="provenance_repair_acceptance")

    if not sql_surface:
        issues.append("no SQL surface selected")
    if not qdrant_surface:
        issues.append("no Qdrant surface selected")
    if not rehydrate_surface:
        issues.append("no rehydrate surface selected")
    if not provenance_surface:
        issues.append("no provenance surface selected")

    plan = {
        "schema": SQL_QDRANT_PROJECTION_PLAN_SCHEMA,
        "bloc": "F",
        "bloc_name": "sql-qdrant-projection-readiness",
        "readiness_audit_path": str(audit_path),
        "readiness_audit_schema": audit.get("schema"),
        "target_runtime_root": audit.get("target_runtime_root"),
        "target_isolated_runtime_root": audit.get("target_isolated_runtime_root"),
        "source_baseline_ref": audit.get("source_baseline_ref"),
        "source_entry_digest": audit.get("source_entry_digest"),
        "repair_digest": audit.get("repair_digest"),
        "sql_qdrant_projection_plan_ready": not issues,
        "execution_allowed_by_0211": False,
        "sql_write_allowed_by_0211": False,
        "qdrant_write_allowed_by_0211": False,
        "projection_write_allowed_by_0211": False,
        "p0212_may_execute_controlled_projection_acceptance": not issues,
        "planned_next_patch": "0212-controlled_sql_qdrant_projection_acceptance",
        "projection_strategy": "sql_authority_qdrant_projection_sql_ref_rehydrate",
        "sql_authority_surface": sql_surface,
        "qdrant_projection_surface": qdrant_surface,
        "rehydrate_surface": rehydrate_surface,
        "provenance_surface": provenance_surface,
        "projection_contract": audit.get("projection_contract"),
        "planned_projection_steps": [
            {
                "step": "validate_forward_only_provenance_repair",
                "surface": provenance_surface.get("path") if provenance_surface else "",
                "assertion": "provenance repair acceptance is present before projection",
            },
            {
                "step": "select_sql_authority_record",
                "surface": sql_surface.get("path") if sql_surface else "",
                "assertion": "SQL remains durable authority",
            },
            {
                "step": "plan_qdrant_payload",
                "surface": qdrant_surface.get("path") if qdrant_surface else "",
                "payload_contract": "payload carries sql_ref only as durable authority pointer",
            },
            {
                "step": "plan_recall_rehydrate",
                "surface": rehydrate_surface.get("path") if rehydrate_surface else "",
                "assertion": "Qdrant recall rehydrates from SQL before user-facing result",
            },
            {
                "step": "plan_acceptance",
                "output": "controlled_sql_qdrant_projection_acceptance.json",
                "assertion": "P0212 may execute controlled projection acceptance only",
            },
        ],
        "p0212_execution_unlock_requirements": [
            "explicit controlled SQL/Qdrant projection acceptance patch",
            "reuse existing SQL surface",
            "reuse existing Qdrant surface",
            "reuse existing rehydrate surface",
            "Qdrant payload carries sql_ref",
            "SQL remains durable authority",
            "Qdrant remains projection/search/recall only",
            "no new SQL backend",
            "no new Qdrant backend",
            "close Bloc F only after acceptance",
        ],
        "readiness_surface_counts": {
            "sql_surface_count": audit.get("sql_surface_count"),
            "qdrant_surface_count": audit.get("qdrant_surface_count"),
            "rehydrate_surface_count": audit.get("rehydrate_surface_count"),
            "provenance_surface_count": audit.get("provenance_surface_count"),
        },
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
        "runtime_imports_executed_by_0211": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0211": False,
        "routeproxy_prepared_by_0211": False,
        "read_route_frame_called_by_0211": False,
        "writer_permits_requested_by_0211": False,
        "frames_written_by_0211": False,
        "controlproxy_frames_written_by_0211": False,
        "eventbus_instantiated_by_0211": False,
        "network_used_by_0211": False,
        "sql_written_by_0211": False,
        "qdrant_written_by_0211": False,
    }

    if output_path is not None:
        _write_plan(final_output, plan)

    return plan


def _audit_readiness(audit: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if audit.get("schema") != EXPECTED_AUDIT_SCHEMA:
        issues.append("SQL/Qdrant projection readiness audit schema mismatch")
    if audit.get("sql_qdrant_projection_readiness_audit_success") is not True:
        issues.append("sql_qdrant_projection_readiness_audit_success must be true")
    if audit.get("sql_qdrant_projection_plan_allowed_next") is not True:
        issues.append("sql_qdrant_projection_plan_allowed_next must be true")
    if audit.get("planned_next_patch") != "0211-sql_qdrant_projection_plan":
        issues.append("planned_next_patch must be 0211-sql_qdrant_projection_plan")
    if audit.get("issues") not in ([], None):
        issues.append("SQL/Qdrant projection readiness audit issues must be empty")
    if isinstance(audit.get("warnings"), list) and audit.get("warnings"):
        warnings.extend(str(item) for item in audit.get("warnings", []))
    for key in ("sql_surface_count", "qdrant_surface_count", "rehydrate_surface_count", "provenance_surface_count"):
        value = audit.get(key)
        if not isinstance(value, int) or value < 1:
            issues.append(f"{key} must be >= 1")
    contract = audit.get("projection_contract")
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
    if not isinstance(audit.get("source_baseline_ref"), str) or not audit.get("source_baseline_ref"):
        issues.append("source_baseline_ref must be present")
    if not isinstance(audit.get("source_entry_digest"), str) or not audit.get("source_entry_digest"):
        issues.append("source_entry_digest must be present")
    if not isinstance(audit.get("repair_digest"), str) or not audit.get("repair_digest"):
        issues.append("repair_digest must be present")
    if audit.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for flag in FALSE_AUDIT_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _select_surface(surfaces: Any, *, required_token: str) -> dict[str, Any]:
    if not isinstance(surfaces, list):
        return {}
    for surface in surfaces:
        if not isinstance(surface, Mapping):
            continue
        tokens = surface.get("matched_tokens")
        if isinstance(tokens, list) and required_token in tokens and surface.get("path"):
            return {
                "path": str(surface.get("path")),
                "matched_tokens": [str(token) for token in tokens],
                "use_before_new_code": bool(surface.get("use_before_new_code")),
            }
    for surface in surfaces:
        if isinstance(surface, Mapping) and surface.get("path"):
            tokens = surface.get("matched_tokens") if isinstance(surface.get("matched_tokens"), list) else []
            return {
                "path": str(surface.get("path")),
                "matched_tokens": [str(token) for token in tokens],
                "use_before_new_code": bool(surface.get("use_before_new_code")),
            }
    return {}


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SqlQdrantProjectionPlanError("input must be a JSON object")
    return raw


def _write_plan(path: Path, plan: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise SqlQdrantProjectionPlanError("output filename must be sql_qdrant_projection_plan.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan SQL/Qdrant projection.")
    parser.add_argument("--readiness-audit", required=True, help="Path to sql_qdrant_projection_readiness_audit.json.")
    parser.add_argument("--output", help="Optional sql_qdrant_projection_plan.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    plan = plan_sql_qdrant_projection(
        readiness_audit_path=Path(args.readiness_audit),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"sql_qdrant_projection_plan_ready: {plan['sql_qdrant_projection_plan_ready']}")
        print(f"execution_allowed_by_0211: {plan['execution_allowed_by_0211']}")
        print(f"sql_write_allowed_by_0211: {plan['sql_write_allowed_by_0211']}")
        print(f"qdrant_write_allowed_by_0211: {plan['qdrant_write_allowed_by_0211']}")
        print(f"p0212_may_execute_controlled_projection_acceptance: {plan['p0212_may_execute_controlled_projection_acceptance']}")
        print(f"planned_next_patch: {plan['planned_next_patch']}")
        print(f"issues: {len(plan['issues'])}")
        print(f"warnings: {len(plan['warnings'])}")
    return 0 if plan["sql_qdrant_projection_plan_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
