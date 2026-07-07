#!/usr/bin/env python3
"""Plan the first live controlled prototype execution from the 0216 readiness audit.

0217 is the Bloc H prototype live execution plan.

It reads prototype_live_readiness_audit.json from 0216 and writes
prototype_live_execution_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0217 must plan a real controlled execution for P0218, not another contract-only
smoke loop.

0217 does not execute the prototype.
0217 does not write SQL.
0217 does not read SQL records.
0217 does not create Qdrant collections.
0217 does not upsert Qdrant points.
0217 does not query Qdrant semantic results.
0217 does not write Qdrant.
0217 does not add a new SQL backend.
0217 does not add a new Qdrant backend.
0217 does not add a new inference path.
0217 does not rewrite runtime history.
0217 does not execute Scheduler.run.
0217 does not modify Scheduler.run.
0217 does not import runtime handler modules.
0217 does not write ControlProxy or RouteProxy frames.
0217 does not call GitHub API or use network.

P0218 must execute the live controlled path and produce true flags:
sql_written_by_0218, qdrant_written_by_0218, qdrant_queried_by_0218,
sql_record_read_by_0218, rehydration_executed_by_0218,
response_artifact_written_by_0218, and prototype_success.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
from pathlib import Path
from typing import Any, Mapping


PROTOTYPE_LIVE_EXECUTION_PLAN_SCHEMA = "missipy.prototype.live_execution_plan.v1"
EXPECTED_AUDIT_SCHEMA = "missipy.prototype.live_readiness_audit.v1"
DEFAULT_OUTPUT_NAME = "prototype_live_execution_plan.json"

REQUIRED_P0218_TRUE_FLAGS = [
    "sql_written_by_0218",
    "qdrant_written_by_0218",
    "qdrant_queried_by_0218",
    "sql_record_read_by_0218",
    "rehydration_executed_by_0218",
    "response_artifact_written_by_0218",
    "prototype_success",
]

FALSE_AUDIT_FLAGS = (
    "runtime_imports_executed_by_0216",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0216",
    "routeproxy_prepared_by_0216",
    "read_route_frame_called_by_0216",
    "writer_permits_requested_by_0216",
    "frames_written_by_0216",
    "controlproxy_frames_written_by_0216",
    "eventbus_instantiated_by_0216",
    "external_network_used_by_0216",
    "live_qdrant_query_executed_by_0216",
    "qdrant_queried_by_0216",
    "sql_record_read_by_0216",
    "recall_executed_by_0216",
    "sql_write_allowed_by_0216",
    "qdrant_write_allowed_by_0216",
    "sql_written_by_0216",
    "qdrant_written_by_0216",
    "runtime_history_rewritten_by_0216",
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


class PrototypeLiveExecutionPlanError(ValueError):
    """Raised when prototype live execution planning is unsafe."""


def plan_prototype_live_execution(
    *,
    live_readiness_audit_path: Path | str,
    output_path: Path | str | None = None,
    require_qdrant_probe_success: bool = False,
) -> dict[str, Any]:
    """Plan P0218 live controlled prototype execution without executing it."""

    audit_path = Path(live_readiness_audit_path)
    audit = _read_json_file(audit_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_live_readiness(audit, issues, warnings, require_qdrant_probe_success)

    requirements = audit.get("live_requirements") if isinstance(audit.get("live_requirements"), Mapping) else {}
    target_runtime_root = Path(str(audit.get("target_runtime_root", "")))
    prototype_live_root = Path(str(requirements.get("prototype_live_root", target_runtime_root / "prototype-live")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    if not prototype_live_root.is_absolute():
        issues.append("prototype_live_root must be absolute")

    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be prototype_live_execution_plan.json")
    if target_runtime_root.is_absolute() and final_output.is_absolute():
        if not _is_within_or_equal(final_output, target_runtime_root):
            issues.append("prototype live execution plan output must be inside target_runtime_root")

    qdrant_url = str(requirements.get("qdrant_url", "http://127.0.0.1:6333"))
    qdrant_collection = str(requirements.get("qdrant_collection", "autodoc_prototype_live"))
    vector_dimension = int(requirements.get("vector_dimension", 4))
    if vector_dimension < 1:
        issues.append("vector_dimension must be >= 1")
        vector_dimension = 4

    sql_ref = str(audit.get("sql_ref", ""))
    if not sql_ref:
        issues.append("sql_ref must be present")
    qdrant_payload = audit.get("qdrant_payload")
    if not isinstance(qdrant_payload, Mapping) or qdrant_payload.get("sql_ref") != sql_ref:
        issues.append("qdrant_payload.sql_ref must match sql_ref")
        qdrant_payload = {"sql_ref": sql_ref}

    prototype_run_id = _stable_short_digest({
        "schema": PROTOTYPE_LIVE_EXECUTION_PLAN_SCHEMA,
        "sql_ref": sql_ref,
        "integration_digest": audit.get("integration_digest"),
        "projection_digest": audit.get("projection_digest"),
        "prototype_live_root": str(prototype_live_root),
    })
    point_id = _stable_uuidish(prototype_run_id)
    deterministic_vector = _deterministic_vector(sql_ref, vector_dimension)
    sql_dev_store = str(requirements.get("sql_dev_store", prototype_live_root / "prototype_live_sql.jsonl"))
    response_artifact = str(requirements.get("response_artifact", prototype_live_root / "prototype_live_response.json"))

    sql_record = {
        "schema": "missipy.prototype.live_sql_record.v1",
        "prototype_run_id": prototype_run_id,
        "sql_ref": sql_ref,
        "kind": "prototype_live_record",
        "content": "Controlled prototype live record for context recall rehydrate.",
        "source_entry_digest": audit.get("source_entry_digest"),
        "integration_digest": audit.get("integration_digest"),
        "projection_digest": audit.get("projection_digest"),
    }
    qdrant_point = {
        "id": point_id,
        "vector": deterministic_vector,
        "payload": {
            "sql_ref": sql_ref,
            "prototype_run_id": prototype_run_id,
            "source_entry_digest": audit.get("source_entry_digest"),
            "integration_digest": audit.get("integration_digest"),
            "projection_digest": audit.get("projection_digest"),
        },
    }
    qdrant_requests = _qdrant_requests(qdrant_url, qdrant_collection, vector_dimension, qdrant_point)

    plan_success = not issues
    plan = {
        "schema": PROTOTYPE_LIVE_EXECUTION_PLAN_SCHEMA,
        "bloc": "H",
        "bloc_name": "prototype-closure",
        "live_readiness_audit_path": str(audit_path),
        "live_readiness_audit_schema": audit.get("schema"),
        "target_runtime_root": audit.get("target_runtime_root"),
        "target_isolated_runtime_root": audit.get("target_isolated_runtime_root"),
        "prototype_live_root": str(prototype_live_root),
        "prototype_run_id": prototype_run_id,
        "accepted_baseline": "prototype-live-execution-plan-v1",
        "prototype_live_execution_plan_ready": plan_success,
        "execution_allowed_by_0217": False,
        "p0218_may_execute_live_prototype": plan_success,
        "planned_next_patch": "0218-prototype_live_execution_acceptance",
        "target_path": "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact",
        "sql_ref": sql_ref,
        "qdrant_payload": dict(qdrant_payload),
        "projection_digest": audit.get("projection_digest"),
        "integration_digest": audit.get("integration_digest"),
        "source_entry_digest": audit.get("source_entry_digest"),
        "live_requirements": dict(requirements),
        "selected_surfaces": audit.get("selected_surfaces"),
        "sql_dev_store": sql_dev_store,
        "sql_record": sql_record,
        "qdrant_url": qdrant_url,
        "qdrant_collection": qdrant_collection,
        "qdrant_point": qdrant_point,
        "qdrant_requests": qdrant_requests,
        "response_artifact": response_artifact,
        "prototype_expected_result": {
            "sql_written_by_0218": True,
            "qdrant_written_by_0218": True,
            "qdrant_queried_by_0218": True,
            "sql_record_read_by_0218": True,
            "rehydration_executed_by_0218": True,
            "response_artifact_written_by_0218": True,
            "prototype_success": True,
        },
        "p0218_required_true_flags": REQUIRED_P0218_TRUE_FLAGS,
        "planned_live_execution_steps": [
            {
                "step": "create_prototype_live_root",
                "path": str(prototype_live_root),
                "expected_flag": "prototype_live_root_created_by_0218",
            },
            {
                "step": "write_sql_dev_record",
                "path": sql_dev_store,
                "record_sql_ref": sql_ref,
                "expected_flag": "sql_written_by_0218",
            },
            {
                "step": "create_or_recreate_qdrant_collection",
                "url": qdrant_requests["collection_url"],
                "vector_dimension": vector_dimension,
                "expected_flag": "qdrant_collection_ready_by_0218",
            },
            {
                "step": "upsert_qdrant_point",
                "url": qdrant_requests["upsert_url"],
                "payload_sql_ref": sql_ref,
                "expected_flag": "qdrant_written_by_0218",
            },
            {
                "step": "query_qdrant_point",
                "url": qdrant_requests["search_url"],
                "expected_flag": "qdrant_queried_by_0218",
            },
            {
                "step": "extract_sql_ref",
                "from_payload": "qdrant_result.payload.sql_ref",
                "expected_sql_ref": sql_ref,
            },
            {
                "step": "read_sql_dev_record",
                "path": sql_dev_store,
                "expected_flag": "sql_record_read_by_0218",
            },
            {
                "step": "rehydrate_response",
                "source": "sql_dev_record",
                "expected_flag": "rehydration_executed_by_0218",
            },
            {
                "step": "write_response_artifact",
                "path": response_artifact,
                "expected_flag": "response_artifact_written_by_0218",
            },
        ],
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
        "runtime_imports_executed_by_0217": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0217": False,
        "routeproxy_prepared_by_0217": False,
        "read_route_frame_called_by_0217": False,
        "writer_permits_requested_by_0217": False,
        "frames_written_by_0217": False,
        "controlproxy_frames_written_by_0217": False,
        "eventbus_instantiated_by_0217": False,
        "network_used_by_0217": False,
        "external_network_used_by_0217": False,
        "live_qdrant_query_executed_by_0217": False,
        "qdrant_queried_by_0217": False,
        "sql_record_read_by_0217": False,
        "recall_executed_by_0217": False,
        "sql_write_allowed_by_0217": False,
        "qdrant_write_allowed_by_0217": False,
        "sql_written_by_0217": False,
        "qdrant_written_by_0217": False,
        "runtime_history_rewritten_by_0217": False,
    }

    if output_path is not None:
        _write_plan(final_output, plan)

    return plan


def _audit_live_readiness(
    audit: Mapping[str, Any],
    issues: list[str],
    warnings: list[str],
    require_qdrant_probe_success: bool,
) -> None:
    if audit.get("schema") != EXPECTED_AUDIT_SCHEMA:
        issues.append("prototype live readiness audit schema mismatch")
    if audit.get("prototype_live_readiness_audit_success") is not True:
        issues.append("prototype_live_readiness_audit_success must be true")
    if audit.get("prototype_live_execution_plan_allowed_next") is not True:
        issues.append("prototype_live_execution_plan_allowed_next must be true")
    if audit.get("planned_next_patch") != "0217-prototype_live_execution_plan":
        issues.append("planned_next_patch must be 0217-prototype_live_execution_plan")
    if audit.get("issues") not in ([], None):
        issues.append("prototype live readiness audit issues must be empty")
    if isinstance(audit.get("warnings"), list) and audit.get("warnings"):
        warnings.extend(str(item) for item in audit.get("warnings", []))
    if audit.get("target_path") != "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact":
        issues.append("target_path must be live prototype path")
    if audit.get("p0218_required_true_flags") != REQUIRED_P0218_TRUE_FLAGS:
        issues.append("p0218_required_true_flags mismatch")
    requirements = audit.get("live_requirements")
    if not isinstance(requirements, Mapping):
        issues.append("live_requirements must be present")
    else:
        required = {
            "must_write_sql_by_p0218",
            "must_upsert_qdrant_by_p0218",
            "must_query_qdrant_by_p0218",
            "must_read_sql_by_p0218",
            "must_rehydrate_by_p0218",
            "must_write_response_artifact_by_p0218",
            "must_set_prototype_success_by_p0218",
        }
        for key in required:
            if requirements.get(key) is not True:
                issues.append(f"{key} must be true")
    boundary = audit.get("live_boundary")
    if not isinstance(boundary, Mapping):
        issues.append("live_boundary must be present")
    else:
        if boundary.get("local_qdrant_only") is not True:
            issues.append("live_boundary.local_qdrant_only must be true")
        if boundary.get("external_network_allowed") is not False:
            issues.append("live_boundary.external_network_allowed must be false")
        if boundary.get("github_api_allowed") is not False:
            issues.append("live_boundary.github_api_allowed must be false")
    qdrant_probe = audit.get("qdrant_local_probe")
    if require_qdrant_probe_success:
        if not isinstance(qdrant_probe, Mapping) or qdrant_probe.get("probe_success") is not True:
            issues.append("qdrant_local_probe.probe_success must be true when required")
    if audit.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for flag in FALSE_AUDIT_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _deterministic_vector(seed: str, dimension: int) -> list[float]:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    values: list[float] = []
    for index in range(dimension):
        raw = digest[index % len(digest)]
        values.append(round((raw + 1) / 256.0, 6))
    return values


def _stable_short_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _stable_uuidish(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


def _qdrant_requests(qdrant_url: str, collection: str, dimension: int, point: Mapping[str, Any]) -> dict[str, Any]:
    base = qdrant_url.rstrip("/")
    collection_url = f"{base}/collections/{collection}"
    return {
        "collection_url": collection_url,
        "create_collection_request": {
            "method": "PUT",
            "url": collection_url,
            "json": {
                "vectors": {
                    "size": dimension,
                    "distance": "Cosine",
                },
            },
        },
        "upsert_url": f"{collection_url}/points?wait=true",
        "upsert_request": {
            "method": "PUT",
            "url": f"{collection_url}/points?wait=true",
            "json": {
                "points": [dict(point)],
            },
        },
        "search_url": f"{collection_url}/points/search",
        "search_request": {
            "method": "POST",
            "url": f"{collection_url}/points/search",
            "json": {
                "vector": list(point["vector"]),
                "limit": 1,
                "with_payload": True,
                "with_vector": False,
            },
        },
    }


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PrototypeLiveExecutionPlanError("input must be a JSON object")
    return raw


def _write_plan(path: Path, plan: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise PrototypeLiveExecutionPlanError("output filename must be prototype_live_execution_plan.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_within_or_equal(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan prototype live execution.")
    parser.add_argument("--live-readiness-audit", required=True, help="Path to prototype_live_readiness_audit.json.")
    parser.add_argument("--output", help="Optional prototype_live_execution_plan.json output path.")
    parser.add_argument("--require-qdrant-probe-success", action="store_true", help="Require P0216 localhost Qdrant probe success.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    plan = plan_prototype_live_execution(
        live_readiness_audit_path=Path(args.live_readiness_audit),
        output_path=Path(args.output) if args.output else None,
        require_qdrant_probe_success=args.require_qdrant_probe_success,
    )

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"prototype_live_execution_plan_ready: {plan['prototype_live_execution_plan_ready']}")
        print(f"p0218_may_execute_live_prototype: {plan['p0218_may_execute_live_prototype']}")
        print(f"qdrant_collection: {plan['qdrant_collection']}")
        print(f"sql_dev_store: {plan['sql_dev_store']}")
        print(f"response_artifact: {plan['response_artifact']}")
        print(f"planned_next_patch: {plan['planned_next_patch']}")
        print(f"issues: {len(plan['issues'])}")
        print(f"warnings: {len(plan['warnings'])}")
    return 0 if plan["prototype_live_execution_plan_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
