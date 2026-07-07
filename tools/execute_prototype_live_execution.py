#!/usr/bin/env python3
"""Execute and accept the first live controlled prototype from the 0217 plan.

0218 is the Bloc H prototype live execution acceptance patch.

It reads prototype_live_execution_plan.json from 0217, executes the controlled
local prototype path, and writes prototype_live_execution_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0218 executes a real controlled prototype, not another contract-only smoke loop.

0218 performs controlled local SQL write/read using a stdlib sqlite dev store.
0218 performs controlled local Qdrant collection create/recreate.
0218 performs controlled local Qdrant point upsert.
0218 performs controlled local Qdrant query.
0218 extracts payload.sql_ref from Qdrant result.
0218 reads the SQL record by sql_ref.
0218 rehydrates a response artifact.
0218 writes prototype_live_response.json.
0218 must set prototype_success true only when the complete local path succeeds.

0218 only allows localhost Qdrant.
0218 does not call external network.
0218 does not call GitHub API.
0218 does not add a new SQL backend.
0218 does not add a new Qdrant backend.
0218 does not add a new inference path.
0218 does not rewrite runtime history.
0218 does not execute Scheduler.run.
0218 does not modify Scheduler.run.
0218 does not import runtime handler modules.
0218 does not write ControlProxy or RouteProxy frames.

Bloc H live controlled path:
context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read
-> rehydrate -> response artifact.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping


PROTOTYPE_LIVE_EXECUTION_ACCEPTANCE_SCHEMA = "missipy.prototype.live_execution_acceptance.v1"
EXPECTED_PLAN_SCHEMA = "missipy.prototype.live_execution_plan.v1"
DEFAULT_OUTPUT_NAME = "prototype_live_execution_acceptance.json"
REQUIRED_COLLECTION = "autodoc_prototype_live"

REQUIRED_TRUE_FLAGS = (
    "sql_written_by_0218",
    "qdrant_written_by_0218",
    "qdrant_queried_by_0218",
    "sql_record_read_by_0218",
    "rehydration_executed_by_0218",
    "response_artifact_written_by_0218",
    "prototype_success",
)

FALSE_PLAN_FLAGS = (
    "execution_allowed_by_0217",
    "runtime_imports_executed_by_0217",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0217",
    "routeproxy_prepared_by_0217",
    "read_route_frame_called_by_0217",
    "writer_permits_requested_by_0217",
    "frames_written_by_0217",
    "controlproxy_frames_written_by_0217",
    "eventbus_instantiated_by_0217",
    "network_used_by_0217",
    "external_network_used_by_0217",
    "live_qdrant_query_executed_by_0217",
    "qdrant_queried_by_0217",
    "sql_record_read_by_0217",
    "recall_executed_by_0217",
    "sql_write_allowed_by_0217",
    "qdrant_write_allowed_by_0217",
    "sql_written_by_0217",
    "qdrant_written_by_0217",
    "runtime_history_rewritten_by_0217",
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


class PrototypeLiveExecutionAcceptanceError(ValueError):
    """Raised when prototype live execution acceptance input is unsafe."""


def execute_prototype_live_execution(
    *,
    live_execution_plan_path: Path | str,
    output_path: Path | str | None = None,
    timeout_seconds: float = 5.0,
    recreate_qdrant_collection: bool = True,
) -> dict[str, Any]:
    """Execute the live controlled prototype and write acceptance data."""

    plan_path = Path(live_execution_plan_path)
    plan = _read_json_file(plan_path)
    issues: list[str] = []
    warnings: list[str] = []
    step_results: list[dict[str, Any]] = []

    _audit_execution_plan(plan, issues, warnings)

    target_runtime_root = Path(str(plan.get("target_runtime_root", "")))
    prototype_live_root = Path(str(plan.get("prototype_live_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    if not prototype_live_root.is_absolute():
        issues.append("prototype_live_root must be absolute")
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be prototype_live_execution_acceptance.json")
    if target_runtime_root.is_absolute() and final_output.is_absolute():
        if not _is_within_or_equal(final_output, target_runtime_root):
            issues.append("prototype live execution acceptance output must be inside target_runtime_root")

    qdrant_url = str(plan.get("qdrant_url", ""))
    qdrant_local = _validate_local_url(qdrant_url)
    if not qdrant_local["is_local"]:
        issues.append("qdrant_url must target localhost or 127.0.0.1")
    collection = str(plan.get("qdrant_collection", ""))
    if collection != REQUIRED_COLLECTION:
        issues.append(f"qdrant_collection must be {REQUIRED_COLLECTION}")

    qdrant_point = plan.get("qdrant_point")
    if not isinstance(qdrant_point, Mapping):
        issues.append("qdrant_point must be present")
        qdrant_point = {}
    sql_record = plan.get("sql_record")
    if not isinstance(sql_record, Mapping):
        issues.append("sql_record must be present")
        sql_record = {}
    sql_ref = str(plan.get("sql_ref", ""))
    if not sql_ref:
        issues.append("sql_ref must be present")

    sqlite_store = prototype_live_root / "prototype_live_sql.sqlite3"
    jsonl_trace = Path(str(plan.get("sql_dev_store", prototype_live_root / "prototype_live_sql.jsonl")))
    response_artifact_path = Path(str(plan.get("response_artifact", prototype_live_root / "prototype_live_response.json")))

    flags = {
        "prototype_live_root_created_by_0218": False,
        "sql_written_by_0218": False,
        "qdrant_collection_ready_by_0218": False,
        "qdrant_written_by_0218": False,
        "qdrant_queried_by_0218": False,
        "sql_record_read_by_0218": False,
        "rehydration_executed_by_0218": False,
        "response_artifact_written_by_0218": False,
        "prototype_success": False,
    }

    sql_record_read: dict[str, Any] | None = None
    qdrant_query_result: dict[str, Any] | None = None
    extracted_sql_ref = ""

    if not issues:
        try:
            prototype_live_root.mkdir(parents=True, exist_ok=True)
            flags["prototype_live_root_created_by_0218"] = True
            step_results.append({"step": "create_prototype_live_root", "success": True, "path": str(prototype_live_root)})
        except OSError as exc:
            issues.append(f"failed to create prototype_live_root: {exc}")
            step_results.append({"step": "create_prototype_live_root", "success": False, "error": str(exc)})

    if not issues:
        try:
            _write_sqlite_record(sqlite_store, sql_record)
            _append_jsonl_trace(jsonl_trace, sql_record)
            flags["sql_written_by_0218"] = True
            step_results.append({
                "step": "write_sql_dev_record",
                "success": True,
                "sqlite_store": str(sqlite_store),
                "jsonl_trace": str(jsonl_trace),
                "sql_ref": sql_ref,
            })
        except (OSError, sqlite3.Error, TypeError, ValueError) as exc:
            issues.append(f"failed to write SQL dev record: {exc}")
            step_results.append({"step": "write_sql_dev_record", "success": False, "error": str(exc)})

    if not issues:
        collection_result = _ensure_qdrant_collection(
            qdrant_url=qdrant_url,
            collection=collection,
            vector_dimension=_vector_dimension(qdrant_point),
            timeout_seconds=timeout_seconds,
            recreate=recreate_qdrant_collection,
        )
        step_results.append(collection_result)
        if collection_result.get("success") is True:
            flags["qdrant_collection_ready_by_0218"] = True
        else:
            issues.append(f"failed to prepare Qdrant collection: {collection_result.get('error') or collection_result.get('status')}")

    if not issues:
        upsert_result = _qdrant_upsert_point(
            qdrant_url=qdrant_url,
            collection=collection,
            point=qdrant_point,
            timeout_seconds=timeout_seconds,
        )
        step_results.append(upsert_result)
        if upsert_result.get("success") is True:
            flags["qdrant_written_by_0218"] = True
        else:
            issues.append(f"failed to upsert Qdrant point: {upsert_result.get('error') or upsert_result.get('status')}")

    if not issues:
        query_result = _qdrant_query_point(
            qdrant_url=qdrant_url,
            collection=collection,
            vector=list(qdrant_point.get("vector", [])),
            timeout_seconds=timeout_seconds,
        )
        step_results.append(query_result)
        if query_result.get("success") is True:
            flags["qdrant_queried_by_0218"] = True
            qdrant_query_result = query_result
            extracted_sql_ref = _extract_sql_ref_from_qdrant_result(query_result.get("response_json"))
            if extracted_sql_ref != sql_ref:
                issues.append("Qdrant query result payload.sql_ref did not match plan sql_ref")
        else:
            issues.append(f"failed to query Qdrant point: {query_result.get('error') or query_result.get('status')}")

    if not issues:
        try:
            sql_record_read = _read_sqlite_record(sqlite_store, extracted_sql_ref)
            flags["sql_record_read_by_0218"] = True
            step_results.append({
                "step": "read_sql_dev_record",
                "success": True,
                "sqlite_store": str(sqlite_store),
                "sql_ref": extracted_sql_ref,
            })
        except (OSError, sqlite3.Error, LookupError, json.JSONDecodeError) as exc:
            issues.append(f"failed to read SQL dev record: {exc}")
            step_results.append({"step": "read_sql_dev_record", "success": False, "error": str(exc)})

    response_artifact: dict[str, Any] | None = None
    if not issues and sql_record_read is not None:
        response_artifact = {
            "schema": "missipy.prototype.live_response_artifact.v1",
            "prototype_run_id": plan.get("prototype_run_id"),
            "status": "prototype_live_success",
            "sql_ref": extracted_sql_ref,
            "qdrant_collection": collection,
            "qdrant_point_id": qdrant_point.get("id"),
            "qdrant_payload": qdrant_point.get("payload"),
            "sql_record": sql_record_read,
            "rehydrated_content": sql_record_read.get("content"),
            "integration_digest": plan.get("integration_digest"),
            "projection_digest": plan.get("projection_digest"),
            "created_at_unix": time.time(),
        }
        flags["rehydration_executed_by_0218"] = True
        step_results.append({"step": "rehydrate_response", "success": True, "sql_ref": extracted_sql_ref})

    if not issues and response_artifact is not None:
        try:
            response_artifact_path.parent.mkdir(parents=True, exist_ok=True)
            response_artifact_path.write_text(
                json.dumps(response_artifact, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            flags["response_artifact_written_by_0218"] = True
            step_results.append({"step": "write_response_artifact", "success": True, "path": str(response_artifact_path)})
        except OSError as exc:
            issues.append(f"failed to write response artifact: {exc}")
            step_results.append({"step": "write_response_artifact", "success": False, "error": str(exc)})

    flags["prototype_success"] = all(flags[name] for name in REQUIRED_TRUE_FLAGS if name != "prototype_success") and not issues

    acceptance = {
        "schema": PROTOTYPE_LIVE_EXECUTION_ACCEPTANCE_SCHEMA,
        "bloc": "H",
        "bloc_name": "prototype-closure",
        "live_execution_plan_path": str(plan_path),
        "live_execution_plan_schema": plan.get("schema"),
        "target_runtime_root": plan.get("target_runtime_root"),
        "target_isolated_runtime_root": plan.get("target_isolated_runtime_root"),
        "prototype_live_root": str(prototype_live_root),
        "accepted_baseline": "prototype-live-execution-acceptance-v1",
        "prototype_live_execution_accepted": flags["prototype_success"],
        "prototype_success": flags["prototype_success"],
        "bloc_h_complete": flags["prototype_success"],
        "cycle_complete": flags["prototype_success"],
        "phase_re_evaluated": True,
        "next_recommended_patch": "0219-server_git_configuration_runbook",
        "prototype_run_id": plan.get("prototype_run_id"),
        "target_path": plan.get("target_path"),
        "sql_ref": sql_ref,
        "extracted_sql_ref": extracted_sql_ref,
        "sqlite_dev_store": str(sqlite_store),
        "jsonl_trace": str(jsonl_trace),
        "response_artifact_path": str(response_artifact_path),
        "response_artifact": response_artifact,
        "qdrant_url": qdrant_url,
        "qdrant_collection": collection,
        "qdrant_point_id": qdrant_point.get("id"),
        "qdrant_query_result": qdrant_query_result,
        "step_results": step_results,
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
        "runtime_imports_executed_by_0218": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0218": False,
        "routeproxy_prepared_by_0218": False,
        "read_route_frame_called_by_0218": False,
        "writer_permits_requested_by_0218": False,
        "frames_written_by_0218": False,
        "controlproxy_frames_written_by_0218": False,
        "eventbus_instantiated_by_0218": False,
        "network_used_by_0218": True,
        "external_network_used_by_0218": False,
        "runtime_history_rewritten_by_0218": False,
        "qdrant_collection_ready_by_0218": flags["qdrant_collection_ready_by_0218"],
        "live_qdrant_query_executed_by_0218": flags["qdrant_queried_by_0218"],
        **flags,
    }

    if output_path is not None:
        _write_acceptance(final_output, acceptance)

    return acceptance


def _audit_execution_plan(plan: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if plan.get("schema") != EXPECTED_PLAN_SCHEMA:
        issues.append("prototype live execution plan schema mismatch")
    if plan.get("prototype_live_execution_plan_ready") is not True:
        issues.append("prototype_live_execution_plan_ready must be true")
    if plan.get("p0218_may_execute_live_prototype") is not True:
        issues.append("p0218_may_execute_live_prototype must be true")
    if plan.get("planned_next_patch") != "0218-prototype_live_execution_acceptance":
        issues.append("planned_next_patch must be 0218-prototype_live_execution_acceptance")
    if plan.get("issues") not in ([], None):
        issues.append("prototype live execution plan issues must be empty")
    if isinstance(plan.get("warnings"), list) and plan.get("warnings"):
        warnings.extend(str(item) for item in plan.get("warnings", []))
    if plan.get("target_path") != "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact":
        issues.append("target_path must be live prototype path")
    if plan.get("p0218_required_true_flags") != list(REQUIRED_TRUE_FLAGS):
        issues.append("p0218_required_true_flags mismatch")
    expected = plan.get("prototype_expected_result")
    if not isinstance(expected, Mapping):
        issues.append("prototype_expected_result must be present")
    else:
        for flag in REQUIRED_TRUE_FLAGS:
            if expected.get(flag) is not True:
                issues.append(f"prototype_expected_result.{flag} must be true")
    if not isinstance(plan.get("qdrant_requests"), Mapping):
        issues.append("qdrant_requests must be present")
    if not isinstance(plan.get("qdrant_point"), Mapping):
        issues.append("qdrant_point must be present")
    if not isinstance(plan.get("sql_record"), Mapping):
        issues.append("sql_record must be present")
    if plan.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for flag in FALSE_PLAN_FLAGS:
        if plan.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if plan.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _write_sqlite_record(path: Path, record: Mapping[str, Any]) -> None:
    sql_ref = str(record.get("sql_ref", ""))
    if not sql_ref:
        raise ValueError("record.sql_ref must be present")
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS prototype_records ("
            "sql_ref TEXT PRIMARY KEY, "
            "prototype_run_id TEXT NOT NULL, "
            "payload_json TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO prototype_records(sql_ref, prototype_run_id, payload_json) VALUES (?, ?, ?)",
            (sql_ref, str(record.get("prototype_run_id", "")), json.dumps(dict(record), sort_keys=True)),
        )
        conn.commit()


def _read_sqlite_record(path: Path, sql_ref: str) -> dict[str, Any]:
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT payload_json FROM prototype_records WHERE sql_ref = ?",
            (sql_ref,),
        ).fetchone()
    if row is None:
        raise LookupError(f"sql_ref not found: {sql_ref}")
    raw = json.loads(str(row[0]))
    if not isinstance(raw, dict):
        raise LookupError("SQL payload_json must decode to object")
    return raw


def _append_jsonl_trace(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(record), sort_keys=True) + "\n")


def _ensure_qdrant_collection(
    *,
    qdrant_url: str,
    collection: str,
    vector_dimension: int,
    timeout_seconds: float,
    recreate: bool,
) -> dict[str, Any]:
    base = qdrant_url.rstrip("/")
    collection_url = f"{base}/collections/{collection}"
    result = {"step": "create_or_recreate_qdrant_collection", "collection": collection, "url": collection_url, "success": False}
    if recreate:
        delete_result = _http_json("DELETE", collection_url, None, timeout_seconds, allow_404=True)
        result["delete_result"] = delete_result
        if delete_result.get("success") is not True:
            result["error"] = delete_result.get("error") or delete_result.get("status")
            return result
    create_payload = {"vectors": {"size": vector_dimension, "distance": "Cosine"}}
    create_result = _http_json("PUT", collection_url, create_payload, timeout_seconds)
    result["create_result"] = create_result
    result["success"] = create_result.get("success") is True
    if not result["success"]:
        result["error"] = create_result.get("error") or create_result.get("status")
    return result


def _qdrant_upsert_point(
    *,
    qdrant_url: str,
    collection: str,
    point: Mapping[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    url = f"{qdrant_url.rstrip('/')}/collections/{collection}/points?wait=true"
    result = _http_json("PUT", url, {"points": [dict(point)]}, timeout_seconds)
    return {"step": "upsert_qdrant_point", "url": url, "success": result.get("success") is True, "http_result": result}


def _qdrant_query_point(
    *,
    qdrant_url: str,
    collection: str,
    vector: list[Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    url = f"{qdrant_url.rstrip('/')}/collections/{collection}/points/search"
    payload = {"vector": vector, "limit": 1, "with_payload": True, "with_vector": False}
    result = _http_json("POST", url, payload, timeout_seconds)
    response_json = result.get("json") if isinstance(result.get("json"), Mapping) else {}
    success = result.get("success") is True and bool(_extract_sql_ref_from_qdrant_result(response_json))
    return {
        "step": "query_qdrant_point",
        "url": url,
        "success": success,
        "http_result": result,
        "response_json": response_json,
    }


def _http_json(
    method: str,
    url: str,
    payload: Mapping[str, Any] | None,
    timeout_seconds: float,
    *,
    allow_404: bool = False,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(dict(payload)).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace")
            parsed: Any = {}
            if body:
                try:
                    parsed = json.loads(body)
                except json.JSONDecodeError:
                    parsed = {"raw": body[:500]}
            return {
                "success": 200 <= response.status < 300,
                "status": response.status,
                "body_preview": body[:500],
                "json": parsed,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "success": allow_404 and exc.code == 404,
            "status": exc.code,
            "body_preview": body[:500],
            "json": _safe_json(body),
            "error": "" if allow_404 and exc.code == 404 else str(exc),
        }
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        return {"success": False, "status": "error", "error": str(exc), "json": {}}


def _safe_json(body: str) -> Any:
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"raw": body[:500]}


def _extract_sql_ref_from_qdrant_result(response: Any) -> str:
    if not isinstance(response, Mapping):
        return ""
    result = response.get("result")
    candidate: Any = None
    if isinstance(result, list) and result:
        candidate = result[0]
    elif isinstance(result, Mapping):
        points = result.get("points")
        if isinstance(points, list) and points:
            candidate = points[0]
    if not isinstance(candidate, Mapping):
        return ""
    payload = candidate.get("payload")
    if not isinstance(payload, Mapping):
        return ""
    sql_ref = payload.get("sql_ref")
    return str(sql_ref) if sql_ref else ""


def _vector_dimension(point: Mapping[str, Any]) -> int:
    vector = point.get("vector")
    if isinstance(vector, list) and vector:
        return len(vector)
    return 4


def _validate_local_url(url: str) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    return {
        "url": url,
        "scheme": parsed.scheme,
        "host": host,
        "port": parsed.port,
        "is_local": parsed.scheme in {"http", "https"} and host in {"127.0.0.1", "localhost", "::1"},
    }


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PrototypeLiveExecutionAcceptanceError("input must be a JSON object")
    return raw


def _write_acceptance(path: Path, acceptance: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise PrototypeLiveExecutionAcceptanceError("output filename must be prototype_live_execution_acceptance.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(acceptance, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_within_or_equal(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute prototype live acceptance.")
    parser.add_argument("--live-execution-plan", required=True, help="Path to prototype_live_execution_plan.json.")
    parser.add_argument("--output", help="Optional prototype_live_execution_acceptance.json output path.")
    parser.add_argument("--timeout-seconds", type=float, default=5.0, help="Local Qdrant timeout.")
    parser.add_argument("--no-recreate-qdrant-collection", action="store_true", help="Do not delete/recreate dedicated prototype Qdrant collection.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    acceptance = execute_prototype_live_execution(
        live_execution_plan_path=Path(args.live_execution_plan),
        output_path=Path(args.output) if args.output else None,
        timeout_seconds=args.timeout_seconds,
        recreate_qdrant_collection=not args.no_recreate_qdrant_collection,
    )

    if args.format == "json":
        print(json.dumps(acceptance, indent=2, sort_keys=True))
    else:
        print(f"prototype_live_execution_accepted: {acceptance['prototype_live_execution_accepted']}")
        print(f"prototype_success: {acceptance['prototype_success']}")
        print(f"sql_written_by_0218: {acceptance['sql_written_by_0218']}")
        print(f"qdrant_written_by_0218: {acceptance['qdrant_written_by_0218']}")
        print(f"qdrant_queried_by_0218: {acceptance['qdrant_queried_by_0218']}")
        print(f"sql_record_read_by_0218: {acceptance['sql_record_read_by_0218']}")
        print(f"rehydration_executed_by_0218: {acceptance['rehydration_executed_by_0218']}")
        print(f"response_artifact_written_by_0218: {acceptance['response_artifact_written_by_0218']}")
        print(f"response_artifact_path: {acceptance['response_artifact_path']}")
        print(f"issues: {len(acceptance['issues'])}")
    return 0 if acceptance["prototype_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
