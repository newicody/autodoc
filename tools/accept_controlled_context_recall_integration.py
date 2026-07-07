#!/usr/bin/env python3
"""Accept controlled context recall integration from the 0214 plan.

0215 is the Bloc G controlled context recall integration acceptance patch.

It reads context_recall_integration_plan.json from 0214 and writes
controlled_context_recall_integration_acceptance.json only.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0215 must reuse the 0214 context recall integration plan and audited existing
surfaces.

0215 explicitly unlocks controlled context recall integration acceptance for this
phase only.

0215 does not perform live Qdrant recall.
0215 does not query Qdrant.
0215 does not read SQL records.
0215 does not write SQL.
0215 does not write Qdrant.
0215 does not add a new SQL backend.
0215 does not add a new Qdrant backend.
0215 does not add a new inference path.
0215 does not rewrite runtime history.
0215 does not execute Scheduler.run.
0215 does not modify Scheduler.run.
0215 does not import runtime handler modules.
0215 does not call handle_scheduler_route_command.
0215 does not call handle_scheduler_route_request.
0215 does not call prepare_route_proxy_runtime.
0215 does not call read_route_frame.
0215 does not request writer permits.
0215 does not call write_route_frame.
0215 does not write ControlProxy or RouteProxy frames.
0215 does not call GitHub API or use network.

Bloc G target path is context/query -> Qdrant recall -> sql_ref -> SQL rehydrate
-> response artifact.
0215 closes Bloc G by writing controlled_context_recall_integration_acceptance.json only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


CONTROLLED_CONTEXT_RECALL_INTEGRATION_ACCEPTANCE_SCHEMA = (
    "missipy.context_recall.controlled_integration_acceptance.v1"
)
EXPECTED_PLAN_SCHEMA = "missipy.context_recall.integration_plan.v1"
DEFAULT_OUTPUT_NAME = "controlled_context_recall_integration_acceptance.json"

FALSE_PLAN_FLAGS = (
    "execution_allowed_by_0214",
    "recall_execution_allowed_by_0214",
    "qdrant_query_allowed_by_0214",
    "sql_record_read_allowed_by_0214",
    "sql_write_allowed_by_0214",
    "qdrant_write_allowed_by_0214",
    "runtime_imports_executed_by_0214",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0214",
    "routeproxy_prepared_by_0214",
    "read_route_frame_called_by_0214",
    "writer_permits_requested_by_0214",
    "frames_written_by_0214",
    "controlproxy_frames_written_by_0214",
    "eventbus_instantiated_by_0214",
    "network_used_by_0214",
    "sql_record_read_by_0214",
    "qdrant_queried_by_0214",
    "recall_executed_by_0214",
    "sql_written_by_0214",
    "qdrant_written_by_0214",
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


class ControlledContextRecallIntegrationAcceptanceError(ValueError):
    """Raised when controlled context recall integration acceptance is unsafe."""


def accept_controlled_context_recall_integration(
    *,
    integration_plan_path: Path | str,
    repo_root: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Accept controlled context recall integration without live recall or SQL read."""

    plan_path = Path(integration_plan_path)
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
        issues.append("output filename must be controlled_context_recall_integration_acceptance.json")
    if target_runtime_root.is_absolute() and final_output.is_absolute():
        if not _is_within_or_equal(final_output, target_runtime_root):
            issues.append("controlled context recall acceptance output must be inside target_runtime_root")

    selected_surfaces = _selected_surfaces(plan)
    _audit_selected_surfaces(root, selected_surfaces, issues)

    sql_ref = str(plan.get("sql_ref", ""))
    qdrant_payload = plan.get("qdrant_payload")
    if not isinstance(qdrant_payload, Mapping):
        issues.append("qdrant_payload must be present")
        qdrant_payload = {}
    elif qdrant_payload.get("sql_ref") != sql_ref:
        issues.append("qdrant_payload.sql_ref must match sql_ref")
    if not sql_ref:
        issues.append("sql_ref must be present")

    controlled_context_query_artifact = {
        "kind": "context_query_artifact",
        "query_ref": "controlled-context-recall-smoke",
        "target_path": plan.get("target_path"),
        "sql_ref": sql_ref,
        "surface": plan.get("context_query_surface"),
    }
    controlled_recall_result = {
        "kind": "controlled_recall_result",
        "mode": "contractual_no_live_qdrant_query",
        "sql_ref": sql_ref,
        "qdrant_payload": dict(qdrant_payload),
        "surface": plan.get("recall_surface"),
        "live_qdrant_query_executed": False,
    }
    controlled_rehydrate_result = {
        "kind": "controlled_rehydrate_result",
        "mode": "contractual_no_sql_record_read",
        "sql_ref": sql_ref,
        "surface": plan.get("rehydrate_surface"),
        "sql_record_read": False,
    }
    response_artifact = {
        "kind": "response_artifact",
        "status": "controlled_context_recall_contract_accepted",
        "sql_ref": sql_ref,
        "rehydration_required": True,
        "surface": plan.get("response_surface"),
    }
    integration_record = {
        "integration_strategy": plan.get("integration_strategy"),
        "target_path": plan.get("target_path"),
        "context_query_artifact": controlled_context_query_artifact,
        "controlled_recall_result": controlled_recall_result,
        "controlled_rehydrate_result": controlled_rehydrate_result,
        "response_artifact": response_artifact,
        "sql_role": "durable authority",
        "qdrant_role": "projection/search/recall only",
        "live_qdrant_query_executed": False,
        "sql_record_read": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
    }
    integration_digest = _stable_digest(integration_record)

    accepted = not issues
    acceptance = {
        "schema": CONTROLLED_CONTEXT_RECALL_INTEGRATION_ACCEPTANCE_SCHEMA,
        "bloc": "G",
        "bloc_name": "context-recall-integration",
        "integration_plan_path": str(plan_path),
        "integration_plan_schema": plan.get("schema"),
        "target_runtime_root": plan.get("target_runtime_root"),
        "target_isolated_runtime_root": plan.get("target_isolated_runtime_root"),
        "accepted_baseline": "controlled-context-recall-integration-contract-v1",
        "controlled_context_recall_integration_accepted": accepted,
        "context_recall_integration_contract_accepted": accepted,
        "controlled_context_recall_acceptance_executed": True,
        "bloc_g_complete": accepted,
        "phase_re_evaluated": True,
        "next_bloc": "H",
        "next_bloc_name": "prototype-closure",
        "next_recommended_patch": "0216-prototype_readiness_audit",
        "execution_unlocked_by_0215": True,
        "execution_allowed_by_0215": True,
        "integration_strategy": plan.get("integration_strategy"),
        "target_path": plan.get("target_path"),
        "sql_ref": sql_ref,
        "qdrant_payload": dict(qdrant_payload),
        "payload_contains_sql_ref": bool(sql_ref) and dict(qdrant_payload).get("sql_ref") == sql_ref,
        "rehydration_required": True,
        "context_query_artifact": controlled_context_query_artifact,
        "controlled_recall_result": controlled_recall_result,
        "controlled_rehydrate_result": controlled_rehydrate_result,
        "response_artifact": response_artifact,
        "integration_record": integration_record,
        "integration_digest": integration_digest,
        "selected_surfaces": selected_surfaces,
        "projection_digest": plan.get("projection_digest"),
        "source_entry_digest": plan.get("source_entry_digest"),
        "repair_digest": plan.get("repair_digest"),
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
        "runtime_imports_executed_by_0215": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0215": False,
        "routeproxy_prepared_by_0215": False,
        "read_route_frame_called_by_0215": False,
        "writer_permits_requested_by_0215": False,
        "frames_written_by_0215": False,
        "controlproxy_frames_written_by_0215": False,
        "eventbus_instantiated_by_0215": False,
        "network_used_by_0215": False,
        "live_qdrant_query_executed_by_0215": False,
        "qdrant_queried_by_0215": False,
        "sql_record_read_by_0215": False,
        "recall_executed_by_0215": False,
        "sql_write_allowed_by_0215": False,
        "qdrant_write_allowed_by_0215": False,
        "sql_written_by_0215": False,
        "qdrant_written_by_0215": False,
        "runtime_history_rewritten_by_0215": False,
    }

    _write_acceptance(final_output, acceptance)
    return acceptance


def _audit_plan(plan: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if plan.get("schema") != EXPECTED_PLAN_SCHEMA:
        issues.append("context recall integration plan schema mismatch")
    if plan.get("context_recall_integration_plan_ready") is not True:
        issues.append("context_recall_integration_plan_ready must be true")
    if plan.get("integration_strategy") != "context_query_qdrant_recall_sql_ref_sql_rehydrate_response_artifact":
        issues.append("integration_strategy must be context_query_qdrant_recall_sql_ref_sql_rehydrate_response_artifact")
    if plan.get("target_path") != "context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact":
        issues.append("target_path must be context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact")
    if plan.get("p0215_may_execute_controlled_context_recall_acceptance") is not True:
        issues.append("p0215_may_execute_controlled_context_recall_acceptance must be true")
    if plan.get("planned_next_patch") != "0215-controlled_context_recall_integration_acceptance":
        issues.append("planned_next_patch must be 0215-controlled_context_recall_integration_acceptance")
    if plan.get("issues") not in ([], None):
        issues.append("context recall integration plan issues must be empty")
    if isinstance(plan.get("warnings"), list) and plan.get("warnings"):
        warnings.extend(str(item) for item in plan.get("warnings", []))
    contract = plan.get("integration_contract")
    if not isinstance(contract, Mapping):
        issues.append("integration_contract must be present")
    else:
        if contract.get("recall") != "Qdrant recall returns sql_ref":
            issues.append("integration_contract recall must require sql_ref")
        if contract.get("rehydration") != "SQL authority hydrates sql_ref":
            issues.append("integration_contract rehydration must require SQL authority")
        if contract.get("output") != "response/result artifact":
            issues.append("integration_contract output must be response/result artifact")
    if not isinstance(plan.get("sql_ref"), str) or not plan.get("sql_ref"):
        issues.append("sql_ref must be present")
    payload = plan.get("qdrant_payload")
    if not isinstance(payload, Mapping) or payload.get("sql_ref") != plan.get("sql_ref"):
        issues.append("qdrant_payload.sql_ref must match sql_ref")
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
        "context_query_surface": _surface_mapping(plan.get("context_query_surface")),
        "recall_surface": _surface_mapping(plan.get("recall_surface")),
        "rehydrate_surface": _surface_mapping(plan.get("rehydrate_surface")),
        "response_surface": _surface_mapping(plan.get("response_surface")),
        "projection_surface": _surface_mapping(plan.get("projection_surface")),
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
        raise ControlledContextRecallIntegrationAcceptanceError("input must be a JSON object")
    return raw


def _write_acceptance(path: Path, acceptance: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ControlledContextRecallIntegrationAcceptanceError(
            "output filename must be controlled_context_recall_integration_acceptance.json"
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
    parser = argparse.ArgumentParser(description="Accept controlled context recall integration.")
    parser.add_argument("--integration-plan", required=True, help="Path to context_recall_integration_plan.json.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--output", help="Optional controlled_context_recall_integration_acceptance.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    acceptance = accept_controlled_context_recall_integration(
        integration_plan_path=Path(args.integration_plan),
        repo_root=Path(args.repo_root),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(acceptance, indent=2, sort_keys=True))
    else:
        print(f"controlled_context_recall_integration_accepted: {acceptance['controlled_context_recall_integration_accepted']}")
        print(f"bloc_g_complete: {acceptance['bloc_g_complete']}")
        print(f"payload_contains_sql_ref: {acceptance['payload_contains_sql_ref']}")
        print(f"live_qdrant_query_executed_by_0215: {acceptance['live_qdrant_query_executed_by_0215']}")
        print(f"sql_record_read_by_0215: {acceptance['sql_record_read_by_0215']}")
        print(f"next_bloc: {acceptance['next_bloc']}")
        print(f"issues: {len(acceptance['issues'])}")
    return 0 if acceptance["controlled_context_recall_integration_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
