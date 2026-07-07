#!/usr/bin/env python3
"""Plan context recall integration from the 0213 audit.

0214 is the Bloc G context recall integration plan only.

It reads context_recall_integration_audit.json from 0213 and writes
context_recall_integration_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0214 must reuse the 0213 context recall integration audit before any
context/recall/rehydrate execution is allowed.

0214 does not execute recall.
0214 does not query Qdrant.
0214 does not read SQL records.
0214 does not write SQL.
0214 does not write Qdrant.
0214 does not add a new SQL backend.
0214 does not add a new Qdrant backend.
0214 does not add a new inference path.
0214 does not rewrite runtime history.
0214 does not execute Scheduler.run.
0214 does not modify Scheduler.run.
0214 does not import runtime handler modules.
0214 does not call handle_scheduler_route_command.
0214 does not call handle_scheduler_route_request.
0214 does not call prepare_route_proxy_runtime.
0214 does not call read_route_frame.
0214 does not request writer permits.
0214 does not call write_route_frame.
0214 does not write ControlProxy or RouteProxy frames.
0214 does not call GitHub API or use network.

Bloc G target path is context/query -> Qdrant recall -> sql_ref -> SQL rehydrate
-> response artifact.
0214 plans integration only; P0215 may execute controlled context recall
integration acceptance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


CONTEXT_RECALL_INTEGRATION_PLAN_SCHEMA = "missipy.context_recall.integration_plan.v1"
EXPECTED_AUDIT_SCHEMA = "missipy.context_recall.integration_audit.v1"
DEFAULT_OUTPUT_NAME = "context_recall_integration_plan.json"

FALSE_AUDIT_FLAGS = (
    "runtime_imports_executed_by_0213",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0213",
    "routeproxy_prepared_by_0213",
    "read_route_frame_called_by_0213",
    "writer_permits_requested_by_0213",
    "frames_written_by_0213",
    "controlproxy_frames_written_by_0213",
    "eventbus_instantiated_by_0213",
    "network_used_by_0213",
    "sql_record_read_by_0213",
    "qdrant_queried_by_0213",
    "recall_executed_by_0213",
    "sql_written_by_0213",
    "qdrant_written_by_0213",
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


class ContextRecallIntegrationPlanError(ValueError):
    """Raised when context recall integration planning is unsafe."""


def plan_context_recall_integration(
    *,
    integration_audit_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Plan context recall integration without executing recall."""

    audit_path = Path(integration_audit_path)
    audit = _read_json_file(audit_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_integration_audit(audit, issues, warnings)

    target_runtime_root = Path(str(audit.get("target_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be context_recall_integration_plan.json")

    context_surface = _select_surface(audit.get("context_surfaces"), preferred_tokens=("query", "artifact", "context"))
    recall_surface = _select_surface(audit.get("recall_surfaces"), preferred_tokens=("recall", "Qdrant", "qdrant"))
    rehydrate_surface = _select_surface(audit.get("rehydrate_surfaces"), preferred_tokens=("rehydrate", "get_record", "sql_ref"))
    response_surface = _select_surface(audit.get("response_surfaces"), preferred_tokens=("response", "result", "to_mapping"))
    projection_surface = _select_surface(audit.get("projection_surfaces"), preferred_tokens=("controlled_sql_qdrant_projection_acceptance", "qdrant_payload", "sql_ref"))

    if not context_surface:
        issues.append("no context/query surface selected")
    if not recall_surface:
        issues.append("no recall/Qdrant surface selected")
    if not rehydrate_surface:
        issues.append("no rehydrate/sql_ref surface selected")
    if not response_surface:
        issues.append("no response/result surface selected")
    if not projection_surface:
        issues.append("no projection/sql_ref surface selected")

    plan = {
        "schema": CONTEXT_RECALL_INTEGRATION_PLAN_SCHEMA,
        "bloc": "G",
        "bloc_name": "context-recall-integration",
        "integration_audit_path": str(audit_path),
        "integration_audit_schema": audit.get("schema"),
        "target_runtime_root": audit.get("target_runtime_root"),
        "target_isolated_runtime_root": audit.get("target_isolated_runtime_root"),
        "sql_ref": audit.get("sql_ref"),
        "qdrant_payload": audit.get("qdrant_payload"),
        "projection_digest": audit.get("projection_digest"),
        "source_entry_digest": audit.get("source_entry_digest"),
        "repair_digest": audit.get("repair_digest"),
        "context_recall_integration_plan_ready": not issues,
        "execution_allowed_by_0214": False,
        "recall_execution_allowed_by_0214": False,
        "qdrant_query_allowed_by_0214": False,
        "sql_record_read_allowed_by_0214": False,
        "sql_write_allowed_by_0214": False,
        "qdrant_write_allowed_by_0214": False,
        "p0215_may_execute_controlled_context_recall_acceptance": not issues,
        "planned_next_patch": "0215-controlled_context_recall_integration_acceptance",
        "integration_strategy": "context_query_qdrant_recall_sql_ref_sql_rehydrate_response_artifact",
        "target_path": "context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact",
        "context_query_surface": context_surface,
        "recall_surface": recall_surface,
        "rehydrate_surface": rehydrate_surface,
        "response_surface": response_surface,
        "projection_surface": projection_surface,
        "integration_contract": audit.get("integration_contract"),
        "planned_integration_steps": [
            {
                "step": "build_context_query_artifact",
                "surface": context_surface.get("path") if context_surface else "",
                "assertion": "context/query artifact is the input boundary",
            },
            {
                "step": "plan_qdrant_recall",
                "surface": recall_surface.get("path") if recall_surface else "",
                "assertion": "Qdrant recall returns sql_ref only",
            },
            {
                "step": "plan_sql_rehydrate",
                "surface": rehydrate_surface.get("path") if rehydrate_surface else "",
                "assertion": "SQL authority hydrates returned sql_ref",
            },
            {
                "step": "plan_response_artifact",
                "surface": response_surface.get("path") if response_surface else "",
                "assertion": "response/result artifact records hydrated context",
            },
            {
                "step": "plan_acceptance",
                "output": "controlled_context_recall_integration_acceptance.json",
                "assertion": "P0215 may execute controlled integration acceptance only",
            },
        ],
        "p0215_execution_unlock_requirements": [
            "explicit controlled context recall integration acceptance patch",
            "reuse context/query surface",
            "reuse recall/Qdrant surface",
            "reuse sql_ref rehydrate surface",
            "reuse response/result artifact surface",
            "qdrant recall result must contain sql_ref",
            "rehydration must be required",
            "SQL remains durable authority",
            "Qdrant remains projection/search/recall only",
            "no new SQL backend",
            "no new Qdrant backend",
            "close Bloc G only after acceptance",
        ],
        "readiness_surface_counts": {
            "context_surface_count": audit.get("context_surface_count"),
            "recall_surface_count": audit.get("recall_surface_count"),
            "rehydrate_surface_count": audit.get("rehydrate_surface_count"),
            "response_surface_count": audit.get("response_surface_count"),
            "projection_surface_count": audit.get("projection_surface_count"),
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
        "runtime_imports_executed_by_0214": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0214": False,
        "routeproxy_prepared_by_0214": False,
        "read_route_frame_called_by_0214": False,
        "writer_permits_requested_by_0214": False,
        "frames_written_by_0214": False,
        "controlproxy_frames_written_by_0214": False,
        "eventbus_instantiated_by_0214": False,
        "network_used_by_0214": False,
        "sql_record_read_by_0214": False,
        "qdrant_queried_by_0214": False,
        "recall_executed_by_0214": False,
        "sql_written_by_0214": False,
        "qdrant_written_by_0214": False,
    }

    if output_path is not None:
        _write_plan(final_output, plan)

    return plan


def _audit_integration_audit(audit: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if audit.get("schema") != EXPECTED_AUDIT_SCHEMA:
        issues.append("context recall integration audit schema mismatch")
    if audit.get("context_recall_integration_audit_success") is not True:
        issues.append("context_recall_integration_audit_success must be true")
    if audit.get("context_recall_integration_plan_allowed_next") is not True:
        issues.append("context_recall_integration_plan_allowed_next must be true")
    if audit.get("planned_next_patch") != "0214-context_recall_integration_plan":
        issues.append("planned_next_patch must be 0214-context_recall_integration_plan")
    if audit.get("issues") not in ([], None):
        issues.append("context recall integration audit issues must be empty")
    if isinstance(audit.get("warnings"), list) and audit.get("warnings"):
        warnings.extend(str(item) for item in audit.get("warnings", []))
    for key in ("context_surface_count", "recall_surface_count", "rehydrate_surface_count", "response_surface_count", "projection_surface_count"):
        value = audit.get(key)
        if not isinstance(value, int) or value < 1:
            issues.append(f"{key} must be >= 1")
    contract = audit.get("integration_contract")
    if not isinstance(contract, Mapping):
        issues.append("integration_contract must be present")
    else:
        if contract.get("recall") != "Qdrant recall returns sql_ref":
            issues.append("integration_contract recall must require sql_ref")
        if contract.get("rehydration") != "SQL authority hydrates sql_ref":
            issues.append("integration_contract rehydration must require SQL authority")
        if contract.get("output") != "response/result artifact":
            issues.append("integration_contract output must be response/result artifact")
    if audit.get("target_path") != "context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact":
        issues.append("target_path must be context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact")
    if not isinstance(audit.get("sql_ref"), str) or not audit.get("sql_ref"):
        issues.append("sql_ref must be present")
    payload = audit.get("qdrant_payload")
    if not isinstance(payload, Mapping) or payload.get("sql_ref") != audit.get("sql_ref"):
        issues.append("qdrant_payload.sql_ref must match sql_ref")
    if not isinstance(audit.get("projection_digest"), str) or not audit.get("projection_digest"):
        issues.append("projection_digest must be present")
    if audit.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for flag in FALSE_AUDIT_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _select_surface(surfaces: Any, *, preferred_tokens: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(surfaces, list):
        return {}
    for token in preferred_tokens:
        for surface in surfaces:
            if not isinstance(surface, Mapping):
                continue
            tokens = surface.get("matched_tokens")
            if isinstance(tokens, list) and token in tokens and surface.get("path"):
                return {
                    "path": str(surface.get("path")),
                    "matched_tokens": [str(item) for item in tokens],
                    "use_before_new_code": bool(surface.get("use_before_new_code")),
                }
    for surface in surfaces:
        if isinstance(surface, Mapping) and surface.get("path"):
            tokens = surface.get("matched_tokens") if isinstance(surface.get("matched_tokens"), list) else []
            return {
                "path": str(surface.get("path")),
                "matched_tokens": [str(item) for item in tokens],
                "use_before_new_code": bool(surface.get("use_before_new_code")),
            }
    return {}


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ContextRecallIntegrationPlanError("input must be a JSON object")
    return raw


def _write_plan(path: Path, plan: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ContextRecallIntegrationPlanError("output filename must be context_recall_integration_plan.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan context recall integration.")
    parser.add_argument("--integration-audit", required=True, help="Path to context_recall_integration_audit.json.")
    parser.add_argument("--output", help="Optional context_recall_integration_plan.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    plan = plan_context_recall_integration(
        integration_audit_path=Path(args.integration_audit),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"context_recall_integration_plan_ready: {plan['context_recall_integration_plan_ready']}")
        print(f"execution_allowed_by_0214: {plan['execution_allowed_by_0214']}")
        print(f"recall_execution_allowed_by_0214: {plan['recall_execution_allowed_by_0214']}")
        print(f"qdrant_query_allowed_by_0214: {plan['qdrant_query_allowed_by_0214']}")
        print(f"sql_record_read_allowed_by_0214: {plan['sql_record_read_allowed_by_0214']}")
        print(f"p0215_may_execute_controlled_context_recall_acceptance: {plan['p0215_may_execute_controlled_context_recall_acceptance']}")
        print(f"planned_next_patch: {plan['planned_next_patch']}")
        print(f"issues: {len(plan['issues'])}")
        print(f"warnings: {len(plan['warnings'])}")
    return 0 if plan["context_recall_integration_plan_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
