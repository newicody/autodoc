#!/usr/bin/env python3
"""Audit provenance repair needs after Bloc D coherence acceptance.

0207 is the Bloc E provenance repair audit only.

It reads controlproxy_routeproxy_coherence_acceptance.json from 0206, inspects
the runtime artifact chain, and writes provenance_repair_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0207 must audit the provenance gap before any provenance repair write is allowed.

0207 does not repair source_baseline_ref.
0207 does not repair source_entry_digest.
0207 does not rewrite controlled_dev_routeproxy_smoke_post_execution_acceptance.json.
0207 does not rewrite runtime history.
0207 does not write SQL.
0207 does not write Qdrant.
0207 does not execute Scheduler.run.
0207 does not modify Scheduler.run.
0207 does not import runtime handler modules.
0207 does not call handle_scheduler_route_command.
0207 does not call handle_scheduler_route_request.
0207 does not call prepare_route_proxy_runtime.
0207 does not call mark_route_frame_stale.
0207 does not call read_route_frame.
0207 does not request writer permits.
0207 does not call write_route_frame.
0207 does not write ControlProxy or RouteProxy frames.
0207 does not call GitHub API or use network.

0207 preserves source_baseline_ref or source_entry_digest missing as an explicit
repair item, not as a blocking runtime failure.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


PROVENANCE_REPAIR_AUDIT_SCHEMA = "missipy.provenance.repair_audit.v1"
EXPECTED_ACCEPTANCE_SCHEMA = "missipy.controlproxy.routeproxy_coherence_acceptance.v1"
DEFAULT_OUTPUT_NAME = "provenance_repair_audit.json"

CHAIN_ARTIFACTS = (
    "controlled_dev_routeproxy_smoke_post_execution_acceptance.json",
    "controlled_dev_routeproxy_smoke_registry.jsonl",
    "scheduler_integration_surface_audit.json",
    "scheduler_hook_dry_run_plan.json",
    "controlled_scheduler_hook_smoke_acceptance.json",
    "controlproxy_contract_audit.json",
    "controlproxy_stale_priority_zone_smoke_plan.json",
    "controlproxy_routeproxy_coherence_acceptance.json",
)

FALSE_ACCEPTANCE_FLAGS = (
    "scheduler_run_executed",
    "scheduler_run_modified",
    "controlproxy_frames_written",
    "scheduler_modified",
    "eventbus_instantiated",
    "network_used",
    "mark_route_frame_stale_called_by_0206",
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


class ProvenanceRepairAuditError(ValueError):
    """Raised when provenance repair audit input is unsafe."""


def audit_provenance_repair(
    *,
    coherence_acceptance_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Audit provenance repair needs without rewriting runtime history."""

    acceptance_path = Path(coherence_acceptance_path)
    acceptance = _read_json_file(acceptance_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_coherence_acceptance(acceptance, issues, warnings)

    target_runtime_root = Path(str(acceptance.get("target_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")

    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be provenance_repair_audit.json")

    chain_reports = _audit_chain_artifacts(target_runtime_root)
    p0200_report = next(
        (
            report
            for report in chain_reports
            if report["name"] == "controlled_dev_routeproxy_smoke_post_execution_acceptance.json"
        ),
        None,
    )

    provenance_items = list(acceptance.get("provenance_repair_items", [])) \
        if isinstance(acceptance.get("provenance_repair_items"), list) else []
    missing_source_baseline_ref = _p0200_field_missing(p0200_report, "source_baseline_ref")
    missing_source_entry_digest = _p0200_field_missing(p0200_report, "source_entry_digest")

    repair_required = bool(provenance_items or missing_source_baseline_ref or missing_source_entry_digest)
    candidate_refs = _collect_candidate_refs(chain_reports)

    audit = {
        "schema": PROVENANCE_REPAIR_AUDIT_SCHEMA,
        "bloc": "E",
        "bloc_name": "sql-qdrant-provenance-repair",
        "coherence_acceptance_path": str(acceptance_path),
        "coherence_acceptance_schema": acceptance.get("schema"),
        "accepted_baseline": acceptance.get("accepted_baseline"),
        "policy_decision_id": acceptance.get("policy_decision_id"),
        "target_runtime_root": acceptance.get("target_runtime_root"),
        "target_isolated_runtime_root": acceptance.get("target_isolated_runtime_root"),
        "provenance_repair_audit_success": not issues,
        "provenance_repair_required": repair_required,
        "source_baseline_ref_missing": missing_source_baseline_ref,
        "source_entry_digest_missing": missing_source_entry_digest,
        "source_baseline_ref_or_source_entry_digest_missing": (
            missing_source_baseline_ref or missing_source_entry_digest
        ),
        "repair_items": _repair_items(
            provenance_items=provenance_items,
            missing_source_baseline_ref=missing_source_baseline_ref,
            missing_source_entry_digest=missing_source_entry_digest,
        ),
        "candidate_provenance_refs": candidate_refs,
        "runtime_chain_artifacts": chain_reports,
        "provenance_repair_plan_allowed_next": not issues,
        "execution_allowed_by_0207": False,
        "sql_write_allowed_by_0207": False,
        "qdrant_write_allowed_by_0207": False,
        "runtime_history_rewrite_allowed_by_0207": False,
        "planned_next_patch": "0208-provenance_repair_plan",
        "repair_boundaries": [
            "P0207 does not repair source_baseline_ref.",
            "P0207 does not repair source_entry_digest.",
            "P0207 does not rewrite runtime history.",
            "P0207 does not write SQL.",
            "P0207 does not write Qdrant.",
            "P0207 only audits provenance repair needs.",
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
        "runtime_imports_executed_by_0207": False,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "handler_called_by_0207": False,
        "routeproxy_prepared_by_0207": False,
        "mark_route_frame_stale_called_by_0207": False,
        "read_route_frame_called_by_0207": False,
        "writer_permits_requested_by_0207": False,
        "frames_written_by_0207": False,
        "controlproxy_frames_written_by_0207": False,
        "eventbus_instantiated_by_0207": False,
        "network_used_by_0207": False,
        "sql_written_by_0207": False,
        "qdrant_written_by_0207": False,
    }

    if output_path is not None:
        _write_audit(final_output, audit)

    return audit


def _audit_coherence_acceptance(
    acceptance: Mapping[str, Any],
    issues: list[str],
    warnings: list[str],
) -> None:
    if acceptance.get("schema") != EXPECTED_ACCEPTANCE_SCHEMA:
        issues.append("P0206 coherence acceptance schema mismatch")
    if acceptance.get("controlproxy_routeproxy_coherence_accepted") is not True:
        issues.append("controlproxy_routeproxy_coherence_accepted must be true")
    if acceptance.get("stale_priority_zone_contract_accepted") is not True:
        issues.append("stale_priority_zone_contract_accepted must be true")
    if acceptance.get("bloc_d_complete") is not True:
        issues.append("bloc_d_complete must be true")
    if acceptance.get("next_bloc") != "E":
        issues.append("next_bloc must be E")
    if acceptance.get("issues") not in ([], None):
        issues.append("P0206 coherence acceptance issues must be empty")
    if isinstance(acceptance.get("warnings"), list) and acceptance.get("warnings"):
        warnings.extend(str(item) for item in acceptance.get("warnings", []))
    if acceptance.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    if acceptance.get("frames_written_count") != 1:
        issues.append("frames_written_count must be 1")
    if acceptance.get("readback_count") != 1:
        issues.append("readback_count must be 1")
    for flag in FALSE_ACCEPTANCE_FLAGS:
        if acceptance.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if acceptance.get(flag) is not False:
            issues.append(f"{flag} must be false")


def _audit_chain_artifacts(target_runtime_root: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for name in CHAIN_ARTIFACTS:
        path = target_runtime_root / name
        report: dict[str, Any] = {
            "name": name,
            "path": str(path),
            "exists": path.exists(),
            "format": "jsonl" if name.endswith(".jsonl") else "json",
            "object_count": 0,
            "schema": "",
            "source_baseline_ref": "",
            "source_entry_digest": "",
            "controlled_dev_baseline_ref": "",
            "accepted_baseline": "",
            "entry_digest": "",
            "entry_ref": "",
            "read_error": "",
        }
        if not path.exists():
            reports.append(report)
            continue
        try:
            if name.endswith(".jsonl"):
                objects = _read_jsonl_file(path)
                report["object_count"] = len(objects)
                if objects:
                    _merge_provenance_fields(report, objects[-1])
            else:
                data = _read_json_file(path)
                report["object_count"] = 1
                _merge_provenance_fields(report, data)
        except Exception as exc:  # pragma: no cover - defensive report payload
            report["read_error"] = str(exc)
        reports.append(report)
    return reports


def _merge_provenance_fields(report: dict[str, Any], data: Mapping[str, Any]) -> None:
    for key in (
        "schema",
        "source_baseline_ref",
        "source_entry_digest",
        "controlled_dev_baseline_ref",
        "accepted_baseline",
        "entry_digest",
        "entry_ref",
        "controlled_dev_baseline_ref",
    ):
        value = data.get(key)
        if isinstance(value, str):
            report[key] = value


def _p0200_field_missing(report: Mapping[str, Any] | None, field: str) -> bool:
    if not report or report.get("exists") is not True:
        return True
    value = report.get(field)
    return not isinstance(value, str) or value == ""


def _collect_candidate_refs(chain_reports: list[Mapping[str, Any]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for report in chain_reports:
        for key in ("controlled_dev_baseline_ref", "entry_ref", "entry_digest", "accepted_baseline"):
            value = report.get(key)
            if isinstance(value, str) and value:
                candidates.append({
                    "artifact": str(report.get("name", "")),
                    "field": key,
                    "value": value,
                })
    return candidates


def _repair_items(
    *,
    provenance_items: list[Any],
    missing_source_baseline_ref: bool,
    missing_source_entry_digest: bool,
) -> list[str]:
    items = [str(item) for item in provenance_items]
    if missing_source_baseline_ref:
        items.append("repair source_baseline_ref in a forward-only provenance repair artifact")
    if missing_source_entry_digest:
        items.append("repair source_entry_digest in a forward-only provenance repair artifact")
    # Keep deterministic unique order.
    unique: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _read_jsonl_file(path: Path) -> list[dict[str, Any]]:
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
        raise ProvenanceRepairAuditError("input must be a JSON object")
    return raw


def _write_audit(path: Path, audit: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ProvenanceRepairAuditError("output filename must be provenance_repair_audit.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit provenance repair needs.")
    parser.add_argument("--coherence-acceptance", required=True, help="Path to controlproxy_routeproxy_coherence_acceptance.json.")
    parser.add_argument("--output", help="Optional provenance_repair_audit.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    audit = audit_provenance_repair(
        coherence_acceptance_path=Path(args.coherence_acceptance),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(f"provenance_repair_audit_success: {audit['provenance_repair_audit_success']}")
        print(f"provenance_repair_required: {audit['provenance_repair_required']}")
        print(f"provenance_repair_plan_allowed_next: {audit['provenance_repair_plan_allowed_next']}")
        print(f"planned_next_patch: {audit['planned_next_patch']}")
        print(f"issues: {len(audit['issues'])}")
        print(f"warnings: {len(audit['warnings'])}")
    return 0 if audit["provenance_repair_audit_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
