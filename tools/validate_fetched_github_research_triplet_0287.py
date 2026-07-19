#!/usr/bin/env python3
"""Validate one locally fetched GitHub research triplet before Scheduler intake.

This operator adapter consumes the existing local fetch-cycle report and one
explicit run id. It reuses:

- the existing ready_run selector and bounded filesystem loader;
- the existing three-artifact assembly and digest validation;
- the existing correlated research work-package builder;
- the existing research admissibility policy.

It performs no GitHub request or mutation, no SQL/Qdrant write, no Scheduler
command creation or dispatch, and no laboratory execution.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from context.github_ready_run_research_admissibility_0287 import (  # noqa: E402
    GitHubReadyRunArtifactContent,
    GitHubReadyRunResearchAdmissibilityCommand,
    assemble_ready_run_and_evaluate_research_admissibility,
)
from tools import assemble_fetched_github_research_admissibility_0287 as fetch_adapter  # noqa: E402

SCHEMA = "missipy.github.fetched_research_triplet_validation.v1"
_FETCH_CYCLE_SCHEMA = "missipy.github_actions.artifact_fetch_cycle_once.v1"
_SCAN_SCHEMA = "missipy.github_actions.artifact_scan_once_live.v1"
_EXPECTED_REPOSITORY = "newicody/projects"
_EXPECTED_STATUS = "Recherche"
_EXPECTED_MODE = "initial"
_EXPECTED_ROLES = (
    "authoritative_request",
    "copilot_advisory",
    "run_manifest",
)


class FetchedResearchTripletValidationError(RuntimeError):
    """Fail-closed validation error before Scheduler-owned intake."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fetch-cycle-report",
        type=Path,
        required=True,
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--state-path", type=Path)
    parser.add_argument(
        "--max-artifact-bytes",
        type=int,
        default=5 * 1024 * 1024,
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(
        tuple(sys.argv[1:] if argv is None else argv)
    )
    output_path = _absolute_output(args.output)
    try:
        payload = validate_fetched_triplet_report(
            fetch_cycle_report=_absolute_input(
                args.fetch_cycle_report
            ),
            run_id=str(args.run_id),
            state_path=(
                None
                if args.state_path is None
                else _absolute_input(args.state_path)
            ),
            max_artifact_bytes=int(args.max_artifact_bytes),
            output_path=output_path,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        payload = {
            "schema": SCHEMA,
            "valid": False,
            "admissible": False,
            "status": "fetched-triplet-invalid",
            "issues": [f"{type(exc).__name__}: {exc}"],
            "run_id": str(args.run_id).strip(),
            "validated_ready_runs": [],
            "scheduler_intake_created": False,
            "boundaries": _boundaries(
                output_requested=True,
            ),
        }

    _write_json_atomic(output_path, payload)
    _emit(payload, str(args.format))
    return 0 if payload.get("valid") is True else 2


def validate_fetched_triplet_report(
    *,
    fetch_cycle_report: Path,
    run_id: str,
    state_path: Path | None,
    max_artifact_bytes: int,
    output_path: Path,
) -> dict[str, Any]:
    normalized_run_id = run_id.strip()
    if not normalized_run_id:
        raise FetchedResearchTripletValidationError(
            "run-id must not be empty"
        )
    if max_artifact_bytes <= 0:
        raise FetchedResearchTripletValidationError(
            "max-artifact-bytes must be > 0"
        )

    issues: list[str] = []
    cycle = fetch_adapter._read_json_mapping(  # noqa: SLF001
        fetch_cycle_report,
        "fetch cycle report",
        issues,
    )
    _validate_fetch_cycle(cycle, issues)

    scan_path = fetch_adapter._scan_report_path(  # noqa: SLF001
        cycle,
        fetch_cycle_report,
        issues,
    )
    scan = (
        fetch_adapter._read_json_mapping(  # noqa: SLF001
            scan_path,
            "artifact scan report",
            issues,
        )
        if scan_path is not None
        else {}
    )
    _validate_scan(scan, issues)

    resolved_state_path = fetch_adapter._resolve_state_path(  # noqa: SLF001
        state_path,
        scan,
        fetch_cycle_report,
    )
    state: Mapping[str, Any] = {}
    if resolved_state_path is not None:
        if resolved_state_path.is_file():
            state = fetch_adapter._read_json_mapping(  # noqa: SLF001
                resolved_state_path,
                "artifact fetch state",
                issues,
            )
        elif not _all_ready_run_records_have_staging(
            cycle,
            scan,
            normalized_run_id,
        ):
            issues.append(
                f"artifact fetch state not found: {resolved_state_path}"
            )

    ready_runs = fetch_adapter._ready_runs(  # noqa: SLF001
        cycle,
        scan,
        (normalized_run_id,),
        issues,
    )
    if len(ready_runs) != 1:
        issues.append(
            "expected exactly one selected ready_run, "
            f"found {len(ready_runs)}"
        )
    if issues:
        raise FetchedResearchTripletValidationError(
            "; ".join(dict.fromkeys(issues))
        )

    ready_run = dict(ready_runs[0])
    loaded, load_issues = fetch_adapter._load_ready_run_contents(  # noqa: SLF001
        ready_run,
        state=state,
        max_artifact_bytes=max_artifact_bytes,
    )
    if load_issues:
        raise FetchedResearchTripletValidationError(
            "; ".join(load_issues)
        )
    if len(loaded) != len(_EXPECTED_ROLES):
        raise FetchedResearchTripletValidationError(
            "expected three locally loaded artifact contents, "
            f"found {len(loaded)}"
        )

    validation = validate_loaded_fetched_triplet(
        ready_run=ready_run,
        loaded_contents=tuple(loaded),
    )
    validation_digest = _validation_digest(
        fetch_cycle_report=fetch_cycle_report,
        ready_run=ready_run,
        validation=validation,
    )
    source_scan = (
        ""
        if scan_path is None
        else str(scan_path.resolve())
    )
    source_state = (
        ""
        if resolved_state_path is None
        else str(resolved_state_path.resolve())
    )
    return {
        "schema": SCHEMA,
        "valid": True,
        "admissible": True,
        "status": "validated-before-scheduler-intake",
        "issues": [],
        "repository": validation["repository"],
        "run_id": validation["run_id"],
        "issue_number": validation["issue_number"],
        "requested_status": validation["requested_status"],
        "request_mode": validation["request_mode"],
        "parent_event_ref": validation["parent_event_ref"],
        "handoff_ref": ready_run["handoff_ref"],
        "validation_digest": validation_digest,
        "fetch_cycle_report": str(fetch_cycle_report.resolve()),
        "artifact_scan_report": source_scan,
        "state_path": source_state,
        "validated_ready_runs": [ready_run],
        "validation": validation,
        "route_candidate": dict(validation["route_candidate"]),
        "counts": {
            "selected_ready_run_count": 1,
            "loaded_artifact_count": len(loaded),
            "validated_role_count": len(_EXPECTED_ROLES),
        },
        "scheduler_intake_created": False,
        "next_action": (
            "the validated ready_run may be handed to the existing "
            "Scheduler-owned intake route"
        ),
        "output": str(output_path),
        "boundaries": _boundaries(
            output_requested=True,
        ),
    }


def validate_loaded_fetched_triplet(
    *,
    ready_run: Mapping[str, Any],
    loaded_contents: tuple[GitHubReadyRunArtifactContent, ...],
) -> dict[str, Any]:
    """Reuse the existing semantic chain and lock the automatic initial route."""
    result = assemble_ready_run_and_evaluate_research_admissibility(
        GitHubReadyRunResearchAdmissibilityCommand(
            ready_run=ready_run,
            artifact_contents=loaded_contents,
        )
    )
    mapping = result.to_mapping()
    if mapping.get("valid") is not True:
        raise FetchedResearchTripletValidationError(
            _result_failure(
                mapping,
                fallback="existing ready_run assembly is invalid",
            )
        )
    if mapping.get("admissible") is not True:
        raise FetchedResearchTripletValidationError(
            _result_failure(
                mapping,
                fallback="fetched research request is inadmissible",
            )
        )
    if mapping.get("status") != "admissible":
        raise FetchedResearchTripletValidationError(
            "existing admissibility result status must be admissible"
        )
    if mapping.get("repository") != _EXPECTED_REPOSITORY:
        raise FetchedResearchTripletValidationError(
            f"repository must be {_EXPECTED_REPOSITORY}"
        )

    run_id = _required_text(mapping, "run_id")
    ready_run_id = _required_text(ready_run, "run_id")
    if run_id != ready_run_id:
        raise FetchedResearchTripletValidationError(
            "validated run_id does not match ready_run"
        )

    artifacts = ready_run.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise FetchedResearchTripletValidationError(
            "ready_run artifacts must be a mapping"
        )
    if set(artifacts) != set(_EXPECTED_ROLES):
        raise FetchedResearchTripletValidationError(
            "ready_run must contain exactly the three expected roles"
        )

    admissibility = _required_mapping(
        mapping,
        "admissibility",
    )
    if admissibility.get("valid") is not True:
        raise FetchedResearchTripletValidationError(
            "existing admissibility mapping must be valid"
        )
    if admissibility.get("admissible") is not True:
        raise FetchedResearchTripletValidationError(
            "existing admissibility mapping must be admissible"
        )
    requested_status = _required_text(
        admissibility,
        "requested_status",
    )
    request_mode = _required_text(
        admissibility,
        "request_mode",
    )
    parent_event_ref = str(
        admissibility.get("parent_event_ref") or ""
    ).strip()
    if requested_status != _EXPECTED_STATUS:
        raise FetchedResearchTripletValidationError(
            "requested_status must be Recherche"
        )
    if request_mode != _EXPECTED_MODE:
        raise FetchedResearchTripletValidationError(
            "automatic research request_mode must be initial"
        )
    if parent_event_ref:
        raise FetchedResearchTripletValidationError(
            "automatic initial research must not carry parent_event_ref"
        )

    issue_number = admissibility.get("issue_number")
    if (
        isinstance(issue_number, bool)
        or not isinstance(issue_number, int)
        or issue_number <= 0
    ):
        raise FetchedResearchTripletValidationError(
            "validated issue_number must be a positive integer"
        )

    route_candidate = _required_mapping(
        admissibility,
        "route_candidate",
    )
    if not _required_text(
        route_candidate,
        "route_candidate_ref",
    ).startswith("research-route-candidate:"):
        raise FetchedResearchTripletValidationError(
            "route_candidate_ref must identify a research route candidate"
        )
    if route_candidate.get("run_id") != run_id:
        raise FetchedResearchTripletValidationError(
            "route candidate run_id mismatch"
        )
    if route_candidate.get("issue_number") != issue_number:
        raise FetchedResearchTripletValidationError(
            "route candidate issue_number mismatch"
        )
    if route_candidate.get("scheduler_command_created") is not False:
        raise FetchedResearchTripletValidationError(
            "validation must not create a Scheduler command"
        )
    if route_candidate.get("scheduler_dispatch_started") is not False:
        raise FetchedResearchTripletValidationError(
            "validation must not dispatch the Scheduler"
        )
    if route_candidate.get("laboratory_execution_started") is not False:
        raise FetchedResearchTripletValidationError(
            "validation must not execute a laboratory"
        )

    run_assembly = _required_mapping(
        mapping,
        "run_assembly",
    )
    work_package_build = _required_mapping(
        mapping,
        "work_package_build",
    )
    if not run_assembly or not work_package_build:
        raise FetchedResearchTripletValidationError(
            "existing correlation evidence must be preserved"
        )

    return {
        "schema": mapping["schema"],
        "valid": True,
        "admissible": True,
        "status": "admissible",
        "repository": mapping["repository"],
        "run_id": run_id,
        "issue_number": issue_number,
        "requested_status": requested_status,
        "request_mode": request_mode,
        "parent_event_ref": parent_event_ref,
        "route_candidate": dict(route_candidate),
        "run_assembly": dict(run_assembly),
        "work_package_build": dict(work_package_build),
        "admissibility": dict(admissibility),
        "existing_ready_run_reused": True,
        "existing_bounded_filesystem_loader_reused": True,
        "existing_dual_artifact_assembly_reused": True,
        "existing_digest_validation_reused": True,
        "existing_correlated_work_package_reused": True,
        "existing_admissibility_gate_reused": True,
        "scheduler_intake_created": False,
    }


def _validate_fetch_cycle(
    cycle: Mapping[str, Any],
    issues: list[str],
) -> None:
    if cycle.get("schema") != _FETCH_CYCLE_SCHEMA:
        issues.append("fetch cycle report schema mismatch")
    if cycle.get("valid") is not True:
        issues.append("fetch cycle report must be valid")
    if cycle.get("mode") != "execute":
        issues.append("fetch cycle report must come from execute mode")
    if cycle.get("status") != "artifacts-fetched":
        issues.append("fetch cycle status must be artifacts-fetched")


def _validate_scan(
    scan: Mapping[str, Any],
    issues: list[str],
) -> None:
    if scan.get("schema") != _SCAN_SCHEMA:
        issues.append("artifact scan report schema mismatch")
    if scan.get("valid") is not True:
        issues.append("artifact scan report must be valid")


def _all_ready_run_records_have_staging(
    cycle: Mapping[str, Any],
    scan: Mapping[str, Any],
    run_id: str,
) -> bool:
    source = cycle.get("ready_runs")
    if not isinstance(source, list):
        source = scan.get("ready_runs")
    if not isinstance(source, list):
        return False
    matches = [
        value
        for value in source
        if isinstance(value, Mapping)
        and str(value.get("run_id", "")).strip() == run_id
    ]
    if len(matches) != 1:
        return False
    artifacts = matches[0].get("artifacts")
    if not isinstance(artifacts, Mapping):
        return False
    if set(artifacts) != set(_EXPECTED_ROLES):
        return False
    return all(
        isinstance(artifacts[role], Mapping)
        and bool(
            str(
                artifacts[role].get("staging_dir", "")
            ).strip()
        )
        for role in _EXPECTED_ROLES
    )


def _validation_digest(
    *,
    fetch_cycle_report: Path,
    ready_run: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> str:
    artifacts = _required_mapping(ready_run, "artifacts")
    artifact_identity = {
        role: {
            "artifact_id": _required_text(
                _required_mapping(artifacts, role),
                "artifact_id",
            ),
            "artifact_name": _required_text(
                _required_mapping(artifacts, role),
                "artifact_name",
            ),
        }
        for role in _EXPECTED_ROLES
    }
    route_candidate = _required_mapping(
        validation,
        "route_candidate",
    )
    payload = {
        "schema": SCHEMA,
        "fetch_cycle_report": str(fetch_cycle_report.resolve()),
        "repository": validation["repository"],
        "run_id": validation["run_id"],
        "issue_number": validation["issue_number"],
        "requested_status": validation["requested_status"],
        "request_mode": validation["request_mode"],
        "parent_event_ref": validation["parent_event_ref"],
        "handoff_ref": ready_run["handoff_ref"],
        "artifacts": artifact_identity,
        "route_candidate_ref": route_candidate["route_candidate_ref"],
        "admissibility_digest": route_candidate.get(
            "admissibility_digest",
            "",
        ),
    }
    canonical = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _result_failure(
    mapping: Mapping[str, Any],
    *,
    fallback: str,
) -> str:
    issues = mapping.get("issues")
    if isinstance(issues, list):
        rendered = [
            str(value).strip()
            for value in issues
            if str(value).strip()
        ]
        if rendered:
            return "; ".join(rendered)
    return fallback


def _required_mapping(
    mapping: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        raise FetchedResearchTripletValidationError(
            f"{key} must be a mapping"
        )
    return value


def _required_text(
    mapping: Mapping[str, Any],
    key: str,
) -> str:
    value = mapping.get(key)
    rendered = value.strip() if isinstance(value, str) else ""
    if not rendered:
        raise FetchedResearchTripletValidationError(
            f"{key} must not be empty"
        )
    return rendered


def _absolute_input(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (
        _REPO_ROOT / path
    ).resolve()


def _absolute_output(path: Path) -> Path:
    return path if path.is_absolute() else _REPO_ROOT / path


def _write_json_atomic(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _boundaries(
    *,
    output_requested: bool,
) -> dict[str, object]:
    return {
        "local_fetch_report_only": True,
        "local_artifact_read_only": True,
        "explicit_run_id_required": True,
        "exact_one_ready_run_required": True,
        "exact_three_artifact_roles_required": True,
        "existing_bounded_filesystem_loader_reused": True,
        "existing_dual_artifact_assembly_reused": True,
        "existing_digest_validation_reused": True,
        "existing_correlated_work_package_reused": True,
        "existing_admissibility_gate_reused": True,
        "automatic_initial_research_only": True,
        "filesystem_write_performed": output_requested,
        "github_request_performed": False,
        "github_mutation_performed": False,
        "workflow_modified": False,
        "actions_artifact_creation_modified": False,
        "sql_write_performed": False,
        "qdrant_write_performed": False,
        "scheduler_intake_created": False,
        "scheduler_command_created": False,
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
        "secret_value_serialized": False,
    }


def _emit(
    payload: Mapping[str, Any],
    output_format: str,
) -> None:
    if output_format == "json":
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return
    counts = payload.get("counts")
    counts = counts if isinstance(counts, Mapping) else {}
    print(
        " ".join(
            (
                f"valid={str(payload.get('valid')).lower()}",
                f"admissible={str(payload.get('admissible')).lower()}",
                f"status={payload.get('status', '')}",
                f"run_id={payload.get('run_id', '')}",
                f"issue_number={payload.get('issue_number', '')}",
                (
                    "loaded_artifacts="
                    f"{counts.get('loaded_artifact_count', 0)}"
                ),
                (
                    "validation_digest="
                    f"{payload.get('validation_digest', '')}"
                ),
            )
        )
    )
    for issue in payload.get("issues", ()):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
