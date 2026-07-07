#!/usr/bin/env python3
"""Audit prototype live readiness after Bloc G controlled integration acceptance.

0216 is the Bloc H prototype live readiness audit.

It reads controlled_context_recall_integration_acceptance.json from 0215, checks
selected repository surfaces, records live execution requirements, optionally
probes a local Qdrant endpoint, and writes prototype_live_readiness_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0216 must prepare a real controlled prototype execution path, not another
contract-only smoke loop.

0216 allows local readiness probing only when explicitly requested.
0216 does not perform live Qdrant recall.
0216 does not upsert Qdrant points.
0216 does not query Qdrant collections for semantic results.
0216 does not read SQL records.
0216 does not write SQL.
0216 does not write Qdrant.
0216 does not add a new SQL backend.
0216 does not add a new Qdrant backend.
0216 does not add a new inference path.
0216 does not rewrite runtime history.
0216 does not execute Scheduler.run.
0216 does not modify Scheduler.run.
0216 does not import runtime handler modules.
0216 does not write ControlProxy or RouteProxy frames.
0216 does not call GitHub API.

Bloc H target is a live controlled prototype:
context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read
-> rehydrate -> response artifact.
P0218 must produce true flags for SQL write/read, Qdrant upsert/query,
rehydration, response artifact, and prototype_success.
"""

from __future__ import annotations

import argparse
import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping


PROTOTYPE_LIVE_READINESS_AUDIT_SCHEMA = "missipy.prototype.live_readiness_audit.v1"
EXPECTED_ACCEPTANCE_SCHEMA = "missipy.context_recall.controlled_integration_acceptance.v1"
DEFAULT_OUTPUT_NAME = "prototype_live_readiness_audit.json"
DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"

FALSE_ACCEPTANCE_FLAGS = (
    "live_qdrant_query_executed_by_0215",
    "qdrant_queried_by_0215",
    "sql_record_read_by_0215",
    "recall_executed_by_0215",
    "sql_write_allowed_by_0215",
    "qdrant_write_allowed_by_0215",
    "sql_written_by_0215",
    "qdrant_written_by_0215",
    "runtime_imports_executed_by_0215",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0215",
    "routeproxy_prepared_by_0215",
    "read_route_frame_called_by_0215",
    "writer_permits_requested_by_0215",
    "frames_written_by_0215",
    "controlproxy_frames_written_by_0215",
    "eventbus_instantiated_by_0215",
    "network_used_by_0215",
    "runtime_history_rewritten_by_0215",
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


class PrototypeLiveReadinessAuditError(ValueError):
    """Raised when prototype live readiness audit input is unsafe."""


def audit_prototype_live_readiness(
    *,
    context_recall_acceptance_path: Path | str,
    repo_root: Path | str,
    output_path: Path | str | None = None,
    qdrant_url: str = DEFAULT_QDRANT_URL,
    probe_local_qdrant: bool = False,
    timeout_seconds: float = 2.0,
) -> dict[str, Any]:
    """Audit readiness for the first real controlled prototype execution."""

    acceptance_path = Path(context_recall_acceptance_path)
    root = Path(repo_root)
    acceptance = _read_json_file(acceptance_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_context_recall_acceptance(acceptance, issues, warnings)

    if not root.exists():
        issues.append("repo_root must exist")
    if not root.is_dir():
        issues.append("repo_root must be a directory")

    target_runtime_root = Path(str(acceptance.get("target_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    prototype_live_root = target_runtime_root / "prototype-live"
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be prototype_live_readiness_audit.json")
    if target_runtime_root.is_absolute() and final_output.is_absolute():
        if not _is_within_or_equal(final_output, target_runtime_root):
            issues.append("prototype live readiness output must be inside target_runtime_root")

    selected_surfaces = _selected_surfaces(acceptance)
    _audit_selected_surfaces(root, selected_surfaces, issues)

    local_qdrant = _validate_local_qdrant_url(qdrant_url)
    if not local_qdrant["is_local"]:
        issues.append("qdrant_url must target localhost or 127.0.0.1 for controlled prototype")
    qdrant_probe = _qdrant_probe(qdrant_url, timeout_seconds) if probe_local_qdrant else {
        "probe_requested": False,
        "probe_success": False,
        "status": "not_requested",
        "url": qdrant_url,
        "local_only": local_qdrant,
    }
    if probe_local_qdrant and qdrant_probe["probe_success"] is not True:
        warnings.append("local Qdrant probe failed; configure/start Qdrant before P0218 live execution")

    sql_ref = str(acceptance.get("sql_ref", ""))
    qdrant_payload = acceptance.get("qdrant_payload")
    if not isinstance(qdrant_payload, Mapping) or qdrant_payload.get("sql_ref") != sql_ref:
        issues.append("qdrant_payload.sql_ref must match sql_ref")
    if not sql_ref:
        issues.append("sql_ref must be present")

    live_requirements = {
        "prototype_live_root": str(prototype_live_root),
        "qdrant_url": qdrant_url,
        "qdrant_collection": "autodoc_prototype_live",
        "sql_dev_store": str(prototype_live_root / "prototype_live_sql.jsonl"),
        "response_artifact": str(prototype_live_root / "prototype_live_response.json"),
        "vector_dimension": 4,
        "vector_mode": "deterministic_test_vector_until_embedding_backend_is_explicitly_selected",
        "must_write_sql_by_p0218": True,
        "must_upsert_qdrant_by_p0218": True,
        "must_query_qdrant_by_p0218": True,
        "must_read_sql_by_p0218": True,
        "must_rehydrate_by_p0218": True,
        "must_write_response_artifact_by_p0218": True,
        "must_set_prototype_success_by_p0218": True,
    }

    audit_success = not issues
    audit = {
        "schema": PROTOTYPE_LIVE_READINESS_AUDIT_SCHEMA,
        "bloc": "H",
        "bloc_name": "prototype-closure",
        "context_recall_acceptance_path": str(acceptance_path),
        "context_recall_acceptance_schema": acceptance.get("schema"),
        "accepted_baseline": acceptance.get("accepted_baseline"),
        "integration_digest": acceptance.get("integration_digest"),
        "projection_digest": acceptance.get("projection_digest"),
        "sql_ref": sql_ref,
        "qdrant_payload": qdrant_payload,
        "target_runtime_root": acceptance.get("target_runtime_root"),
        "target_isolated_runtime_root": acceptance.get("target_isolated_runtime_root"),
        "prototype_live_root": str(prototype_live_root),
        "repo_root": str(root),
        "selected_surfaces": selected_surfaces,
        "live_requirements": live_requirements,
        "qdrant_local_probe": qdrant_probe,
        "prototype_live_readiness_audit_success": audit_success,
        "prototype_live_execution_plan_allowed_next": audit_success,
        "planned_next_patch": "0217-prototype_live_execution_plan",
        "target_path": "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact",
        "p0218_required_true_flags": [
            "sql_written_by_0218",
            "qdrant_written_by_0218",
            "qdrant_queried_by_0218",
            "sql_record_read_by_0218",
            "rehydration_executed_by_0218",
            "response_artifact_written_by_0218",
            "prototype_success",
        ],
        "live_boundary": {
            "local_qdrant_only": True,
            "external_network_allowed": False,
            "github_api_allowed": False,
            "scheduler_run_allowed": False,
            "new_sql_backend_allowed": False,
            "new_qdrant_backend_allowed": False,
            "controlled_sql_write_required_by_p0218": True,
            "controlled_qdrant_write_required_by_p0218": True,
            "controlled_qdrant_query_required_by_p0218": True,
            "controlled_sql_read_required_by_p0218": True,
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
        "runtime_imports_executed_by_0216": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0216": False,
        "routeproxy_prepared_by_0216": False,
        "read_route_frame_called_by_0216": False,
        "writer_permits_requested_by_0216": False,
        "frames_written_by_0216": False,
        "controlproxy_frames_written_by_0216": False,
        "eventbus_instantiated_by_0216": False,
        "network_used_by_0216": bool(probe_local_qdrant),
        "external_network_used_by_0216": False,
        "qdrant_local_probe_executed_by_0216": bool(probe_local_qdrant),
        "live_qdrant_query_executed_by_0216": False,
        "qdrant_queried_by_0216": False,
        "sql_record_read_by_0216": False,
        "recall_executed_by_0216": False,
        "sql_write_allowed_by_0216": False,
        "qdrant_write_allowed_by_0216": False,
        "sql_written_by_0216": False,
        "qdrant_written_by_0216": False,
        "runtime_history_rewritten_by_0216": False,
    }

    if output_path is not None:
        _write_audit(final_output, audit)

    return audit


def _audit_context_recall_acceptance(
    acceptance: Mapping[str, Any],
    issues: list[str],
    warnings: list[str],
) -> None:
    if acceptance.get("schema") != EXPECTED_ACCEPTANCE_SCHEMA:
        issues.append("P0215 controlled context recall integration acceptance schema mismatch")
    if acceptance.get("controlled_context_recall_integration_accepted") is not True:
        issues.append("controlled_context_recall_integration_accepted must be true")
    if acceptance.get("context_recall_integration_contract_accepted") is not True:
        issues.append("context_recall_integration_contract_accepted must be true")
    if acceptance.get("bloc_g_complete") is not True:
        issues.append("bloc_g_complete must be true")
    if acceptance.get("next_bloc") != "H":
        issues.append("next_bloc must be H")
    if acceptance.get("issues") not in ([], None):
        issues.append("P0215 controlled context recall integration acceptance issues must be empty")
    if isinstance(acceptance.get("warnings"), list) and acceptance.get("warnings"):
        warnings.extend(str(item) for item in acceptance.get("warnings", []))
    if acceptance.get("payload_contains_sql_ref") is not True:
        issues.append("payload_contains_sql_ref must be true")
    if acceptance.get("rehydration_required") is not True:
        issues.append("rehydration_required must be true")
    if not isinstance(acceptance.get("integration_digest"), str) or not acceptance.get("integration_digest"):
        issues.append("integration_digest must be present")
    if acceptance.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for flag in FALSE_ACCEPTANCE_FLAGS:
        if acceptance.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if acceptance.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _selected_surfaces(acceptance: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    selected = acceptance.get("selected_surfaces")
    if not isinstance(selected, Mapping):
        return {}
    return {
        "context_query_surface": _surface_mapping(selected.get("context_query_surface")),
        "recall_surface": _surface_mapping(selected.get("recall_surface")),
        "rehydrate_surface": _surface_mapping(selected.get("rehydrate_surface")),
        "response_surface": _surface_mapping(selected.get("response_surface")),
        "projection_surface": _surface_mapping(selected.get("projection_surface")),
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
    for name in ("context_query_surface", "recall_surface", "rehydrate_surface", "response_surface", "projection_surface"):
        surface = selected_surfaces.get(name)
        if not isinstance(surface, Mapping):
            issues.append(f"{name} must be present")
            continue
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


def _validate_local_qdrant_url(url: str) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    return {
        "url": url,
        "scheme": parsed.scheme,
        "host": host,
        "port": parsed.port,
        "is_local": parsed.scheme in {"http", "https"} and host in {"127.0.0.1", "localhost", "::1"},
    }


def _qdrant_probe(url: str, timeout_seconds: float) -> dict[str, Any]:
    local = _validate_local_qdrant_url(url)
    result = {
        "probe_requested": True,
        "probe_success": False,
        "status": "",
        "url": url,
        "collections_url": url.rstrip("/") + "/collections",
        "local_only": local,
        "error": "",
    }
    if not local["is_local"]:
        result["status"] = "rejected_non_local"
        result["error"] = "qdrant_url must be localhost/127.0.0.1"
        return result
    try:
        request = urllib.request.Request(result["collections_url"], method="GET")
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(1024).decode("utf-8", errors="replace")
            result["http_status"] = response.status
            result["body_preview"] = body[:200]
            result["probe_success"] = 200 <= response.status < 500
            result["status"] = "ok" if result["probe_success"] else "bad_status"
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        result["status"] = "error"
        result["error"] = str(exc)
    return result


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PrototypeLiveReadinessAuditError("input must be a JSON object")
    return raw


def _write_audit(path: Path, audit: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise PrototypeLiveReadinessAuditError("output filename must be prototype_live_readiness_audit.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_within_or_equal(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit prototype live readiness.")
    parser.add_argument("--context-recall-acceptance", required=True, help="Path to controlled_context_recall_integration_acceptance.json.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--output", help="Optional prototype_live_readiness_audit.json output path.")
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL, help="Local Qdrant URL; localhost only.")
    parser.add_argument("--probe-local-qdrant", action="store_true", help="Probe local Qdrant /collections endpoint.")
    parser.add_argument("--timeout-seconds", type=float, default=2.0, help="Local Qdrant probe timeout.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    audit = audit_prototype_live_readiness(
        context_recall_acceptance_path=Path(args.context_recall_acceptance),
        repo_root=Path(args.repo_root),
        output_path=Path(args.output) if args.output else None,
        qdrant_url=args.qdrant_url,
        probe_local_qdrant=args.probe_local_qdrant,
        timeout_seconds=args.timeout_seconds,
    )

    if args.format == "json":
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(f"prototype_live_readiness_audit_success: {audit['prototype_live_readiness_audit_success']}")
        print(f"prototype_live_execution_plan_allowed_next: {audit['prototype_live_execution_plan_allowed_next']}")
        print(f"qdrant_local_probe_executed_by_0216: {audit['qdrant_local_probe_executed_by_0216']}")
        print(f"qdrant_local_probe_success: {audit['qdrant_local_probe']['probe_success']}")
        print(f"planned_next_patch: {audit['planned_next_patch']}")
        print(f"issues: {len(audit['issues'])}")
        print(f"warnings: {len(audit['warnings'])}")
    return 0 if audit["prototype_live_readiness_audit_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
