#!/usr/bin/env python3
"""Select one exact local artifact triplet from a duplicated GitHub run.

The normal scan deliberately defers a run when more than one artifact matches
one of the three required roles. This local operator tool resolves only that
specific ambiguity by requiring the exact artifact id for every role.

It never chooses "latest", never contacts GitHub, never deletes dataset state
and never mutates the original fetch or scan report. It writes a new,
compatible fetch-cycle report containing exactly one verified ``ready_run``.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
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

from context.human_readable_artifact_identity_0287 import (  # noqa: E402
    matches_actions_artifact_name,
)
from tools import assemble_fetched_github_research_admissibility_0287 as artifact_loader  # noqa: E402

SCHEMA = "missipy.github_actions.artifact_fetch_cycle_once.v1"
_SCAN_SCHEMA = "missipy.github_actions.artifact_scan_once_live.v1"
_SELECTION_SCHEMA = (
    "missipy.github_actions.explicit_artifact_triplet_selection.v1"
)
_ROLES = {
    "authoritative_request": "autodoc-authoritative-request",
    "copilot_advisory": "autodoc-copilot-advisory",
    "run_manifest": "autodoc-dual-artifact-manifest",
}


class ExplicitArtifactTripletSelectionError(RuntimeError):
    """Raised when exact local selection cannot preserve correlation."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-cycle-report", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--authoritative-request-artifact-id",
        required=True,
    )
    parser.add_argument(
        "--copilot-advisory-artifact-id",
        required=True,
    )
    parser.add_argument(
        "--run-manifest-artifact-id",
        required=True,
    )
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
    try:
        payload = select_explicit_artifact_triplet(
            fetch_cycle_report=_absolute_input(
                args.fetch_cycle_report
            ),
            run_id=str(args.run_id),
            artifact_ids={
                "authoritative_request": str(
                    args.authoritative_request_artifact_id
                ),
                "copilot_advisory": str(
                    args.copilot_advisory_artifact_id
                ),
                "run_manifest": str(
                    args.run_manifest_artifact_id
                ),
            },
            state_path=(
                None
                if args.state_path is None
                else _absolute_input(args.state_path)
            ),
            max_artifact_bytes=int(args.max_artifact_bytes),
            output_path=_absolute_output(args.output),
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        payload = {
            "schema": SCHEMA,
            "selection_schema": _SELECTION_SCHEMA,
            "valid": False,
            "mode": "execute",
            "status": "selection-failed",
            "issues": [f"{type(exc).__name__}: {exc}"],
            "ready_runs": [],
            "boundaries": _boundaries(),
        }

    _write_json_atomic(_absolute_output(args.output), payload)
    _emit(payload, str(args.format))
    return 0 if payload.get("valid") is True else 2


def select_explicit_artifact_triplet(
    *,
    fetch_cycle_report: Path,
    run_id: str,
    artifact_ids: Mapping[str, str],
    state_path: Path | None,
    max_artifact_bytes: int,
    output_path: Path,
) -> dict[str, Any]:
    normalized_run_id = run_id.strip()
    if not normalized_run_id:
        raise ExplicitArtifactTripletSelectionError(
            "run-id must not be empty"
        )
    if max_artifact_bytes <= 0:
        raise ExplicitArtifactTripletSelectionError(
            "max-artifact-bytes must be > 0"
        )

    normalized_ids = _normalize_artifact_ids(artifact_ids)
    issues: list[str] = []
    cycle = artifact_loader._read_json_mapping(  # noqa: SLF001
        fetch_cycle_report,
        "fetch cycle report",
        issues,
    )
    _validate_fetch_cycle(cycle, issues)

    scan_path = artifact_loader._scan_report_path(  # noqa: SLF001
        cycle,
        fetch_cycle_report,
        issues,
    )
    scan = (
        artifact_loader._read_json_mapping(  # noqa: SLF001
            scan_path,
            "artifact scan report",
            issues,
        )
        if scan_path is not None
        else {}
    )
    _validate_scan(scan, issues)

    resolved_state = _state_path(
        explicit=state_path,
        scan=scan,
    )
    state = artifact_loader._read_json_mapping(  # noqa: SLF001
        resolved_state,
        "artifact fetch state",
        issues,
    )

    deferred = _one_duplicate_only_deferred_run(
        scan,
        normalized_run_id,
        issues,
    )
    repository = str(
        deferred.get(
            "repository",
            scan.get("repository", cycle.get("repository", "")),
        )
    ).strip()
    if not repository:
        issues.append("repository is missing")

    records = _available_records(scan, normalized_run_id)
    selected: dict[str, dict[str, Any]] = {}
    for role, legacy_name in _ROLES.items():
        artifact_id = normalized_ids[role]
        matches = [
            record
            for record in records
            if record["artifact_id"] == artifact_id
        ]
        if len(matches) != 1:
            issues.append(
                f"{role} artifact id {artifact_id} must match exactly "
                f"one locally available record, found {len(matches)}"
            )
            continue
        record = dict(matches[0])
        if not matches_actions_artifact_name(
            record["artifact_name"],
            legacy_name,
        ):
            issues.append(
                f"artifact id {artifact_id} does not match role {role}"
            )
            continue
        staging_dir = artifact_loader._staging_dir(  # noqa: SLF001
            record,
            state,
        )
        if staging_dir is None:
            issues.append(
                f"{role} staging directory is unavailable for "
                f"artifact id {artifact_id}"
            )
            continue
        record["staging_dir"] = str(staging_dir)
        record["selection"] = "explicit-artifact-id"
        selected[role] = record

    if issues:
        raise ExplicitArtifactTripletSelectionError(
            "; ".join(issues)
        )

    ready_run = {
        "repository": repository,
        "run_id": normalized_run_id,
        "handoff_ref": (
            "github-actions-ready-run:"
            f"{repository.replace('/', '-')}:{normalized_run_id}"
        ),
        "status": "ready",
        "artifact_count": len(_ROLES),
        "artifacts": selected,
        "selection": {
            "schema": _SELECTION_SCHEMA,
            "mode": "explicit-artifact-ids",
            "source_deferred_reason": "duplicate_roles",
            "artifact_ids": dict(normalized_ids),
            "automatic_latest_selection": False,
            "operator_confirmation_required": True,
        },
        "local_execution_started": False,
        "remote_mutation_performed": False,
    }

    loaded, load_issues = artifact_loader._load_ready_run_contents(  # noqa: SLF001
        ready_run,
        state=state,
        max_artifact_bytes=max_artifact_bytes,
    )
    if load_issues:
        raise ExplicitArtifactTripletSelectionError(
            "; ".join(load_issues)
        )
    if len(loaded) != len(_ROLES):
        raise ExplicitArtifactTripletSelectionError(
            f"expected three verified artifact contents, found {len(loaded)}"
        )

    scan_reference = (
        ""
        if scan_path is None
        else str(scan_path.resolve())
    )
    payload = {
        "schema": SCHEMA,
        "selection_schema": _SELECTION_SCHEMA,
        "valid": True,
        "mode": "execute",
        "status": "artifacts-fetched",
        "issues": [],
        "source_fetch_cycle_report": str(
            fetch_cycle_report.resolve()
        ),
        "source_artifact_scan_report": scan_reference,
        "source_state_path": str(resolved_state.resolve()),
        "reports": {
            "artifact_scan": scan_reference,
        },
        "ready_runs": [ready_run],
        "deferred_runs": [],
        "counts": {
            "ready_run_count": 1,
            "deferred_run_count": 0,
            "selected_artifact_count": len(_ROLES),
        },
        "output": str(output_path),
        "boundaries": _boundaries(),
    }
    return payload


def _normalize_artifact_ids(
    values: Mapping[str, str],
) -> dict[str, str]:
    if set(values) != set(_ROLES):
        raise ExplicitArtifactTripletSelectionError(
            "exactly the three expected artifact roles are required"
        )
    normalized = {
        role: str(values[role]).strip()
        for role in _ROLES
    }
    if any(not value for value in normalized.values()):
        raise ExplicitArtifactTripletSelectionError(
            "every artifact id must be non-empty"
        )
    if len(set(normalized.values())) != len(normalized):
        raise ExplicitArtifactTripletSelectionError(
            "artifact ids must be distinct"
        )
    return normalized


def _validate_fetch_cycle(
    cycle: Mapping[str, Any],
    issues: list[str],
) -> None:
    if cycle.get("schema") != SCHEMA:
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


def _one_duplicate_only_deferred_run(
    scan: Mapping[str, Any],
    run_id: str,
    issues: list[str],
) -> Mapping[str, Any]:
    source = scan.get("deferred_runs")
    if not isinstance(source, list):
        issues.append("artifact scan deferred_runs must be a list")
        return {}
    matches = [
        dict(item)
        for item in source
        if isinstance(item, Mapping)
        and str(item.get("run_id", "")).strip() == run_id
    ]
    if len(matches) != 1:
        issues.append(
            f"run {run_id} must match exactly one deferred run, "
            f"found {len(matches)}"
        )
        return {}
    deferred = matches[0]
    reasons = {
        str(value).strip()
        for value in deferred.get("reasons", ())
    }
    if reasons != {"duplicate_roles"}:
        issues.append(
            "explicit selection is allowed only for duplicate_roles"
        )
    if deferred.get("missing_roles"):
        issues.append("deferred run still has missing roles")
    if deferred.get("unavailable_artifacts"):
        issues.append("deferred run still has unavailable artifacts")
    duplicate_roles = {
        str(value).strip()
        for value in deferred.get("duplicate_roles", ())
    }
    if duplicate_roles != set(_ROLES):
        issues.append(
            "all three roles must be duplicated before explicit selection"
        )
    return deferred


def _available_records(
    scan: Mapping[str, Any],
    run_id: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    downloaded = scan.get("downloaded_artifacts")
    if isinstance(downloaded, list):
        for value in downloaded:
            record = _availability_record(
                value,
                run_id=run_id,
                availability="downloaded",
            )
            if record is not None:
                records.append(record)

    skipped = scan.get("skipped")
    if isinstance(skipped, list):
        for value in skipped:
            if not isinstance(value, Mapping):
                continue
            if str(value.get("reason", "")).strip() != "already_synced":
                continue
            record = _availability_record(
                value,
                run_id=run_id,
                availability="already_synced",
            )
            if record is not None:
                records.append(record)
    return records


def _availability_record(
    value: object,
    *,
    run_id: str,
    availability: str,
) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    record_run_id = str(value.get("run_id", "")).strip()
    artifact_id = str(value.get("artifact_id", "")).strip()
    artifact_name = str(value.get("artifact_name", "")).strip()
    if (
        record_run_id != run_id
        or not artifact_id
        or not artifact_name
    ):
        return None
    record = {
        "run_id": record_run_id,
        "artifact_id": artifact_id,
        "artifact_name": artifact_name,
        "availability": availability,
    }
    staging_dir = str(value.get("staging_dir", "")).strip()
    if staging_dir:
        record["staging_dir"] = staging_dir
    sync_status = str(value.get("sync_status", "")).strip()
    if sync_status:
        record["sync_status"] = sync_status
    return record


def _state_path(
    *,
    explicit: Path | None,
    scan: Mapping[str, Any],
) -> Path:
    if explicit is not None:
        path = explicit
    else:
        raw = str(scan.get("state_path", "")).strip()
        if not raw:
            raise ExplicitArtifactTripletSelectionError(
                "artifact scan state_path is missing"
            )
        path = Path(raw)
        if not path.is_absolute():
            path = _REPO_ROOT / path
    resolved = path.resolve()
    if not resolved.is_file():
        raise ExplicitArtifactTripletSelectionError(
            f"artifact fetch state not found: {resolved}"
        )
    return resolved


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


def _boundaries() -> dict[str, object]:
    return {
        "local_read_only_selection": True,
        "exact_three_artifact_ids_required": True,
        "duplicate_roles_only": True,
        "automatic_latest_selection": False,
        "automatic_historical_fallback": False,
        "source_reports_modified": False,
        "dataset_state_modified": False,
        "github_external_call_performed": False,
        "github_remote_mutation_performed": False,
        "sql_write_performed": False,
        "qdrant_write_performed": False,
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
    ready_runs = payload.get("ready_runs")
    run_id = ""
    if (
        isinstance(ready_runs, list)
        and len(ready_runs) == 1
        and isinstance(ready_runs[0], Mapping)
    ):
        run_id = str(ready_runs[0].get("run_id", ""))
    print(
        " ".join(
            (
                f"valid={str(payload.get('valid')).lower()}",
                f"status={payload.get('status', '')}",
                f"run_id={run_id}",
                (
                    "selected_artifacts="
                    f"{counts.get('selected_artifact_count', 0)}"
                ),
                f"output={payload.get('output', '')}",
            )
        )
    )
    for issue in payload.get("issues", ()):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
