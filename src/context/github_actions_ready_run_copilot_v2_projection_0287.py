"""Resolve one correlated GitHub Actions ready run from the durable raw dataset.

This module is intentionally local-only.  It consumes the scan-once report and
resolves the three already-synchronised artifact members without contacting
GitHub, starting a laboratory, or writing SQL/Qdrant.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

SCAN_REPORT_SCHEMA = "missipy.github_actions.artifact_scan_once_live.v1"
READY_RUN_PROJECTION_INPUT_SCHEMA = (
    "missipy.github_actions.ready_run_copilot_v2_projection_input.v1"
)

_ROLE_FILENAMES = {
    "authoritative_request": "authoritative_request.json",
    "copilot_advisory": "copilot_advisory.json",
    "run_manifest": "dual_artifact_manifest.json",
}


@dataclass(frozen=True, slots=True)
class LocalReadyRunArtifact:
    role: str
    artifact_id: str
    artifact_name: str
    directory: Path
    path: Path

    def to_mapping(self) -> dict[str, str]:
        return {
            "role": self.role,
            "artifact_id": self.artifact_id,
            "artifact_name": self.artifact_name,
            "directory": str(self.directory),
            "path": str(self.path),
        }


@dataclass(frozen=True, slots=True)
class LocalReadyRunProjectionInput:
    repository: str
    run_id: str
    handoff_ref: str
    issue_number: int
    dataset_root: Path
    request: LocalReadyRunArtifact
    advisory: LocalReadyRunArtifact
    manifest: LocalReadyRunArtifact

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": READY_RUN_PROJECTION_INPUT_SCHEMA,
            "repository": self.repository,
            "run_id": self.run_id,
            "handoff_ref": self.handoff_ref,
            "issue_number": self.issue_number,
            "dataset_root": str(self.dataset_root),
            "artifacts": {
                "authoritative_request": self.request.to_mapping(),
                "copilot_advisory": self.advisory.to_mapping(),
                "run_manifest": self.manifest.to_mapping(),
            },
            "durable_raw_dataset_only": True,
            "github_artifact_download_performed": False,
            "laboratory_execution_started": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "remote_mutation_pre_authorized": False,
        }


def resolve_local_ready_run_projection_input(
    *,
    scan_report_path: Path,
    run_id: str,
    dataset_root: Path,
    expected_repository: str = "",
) -> LocalReadyRunProjectionInput:
    """Resolve exactly one ready run and its three durable raw files."""

    report = _load_mapping(scan_report_path, "scan report")
    if report.get("schema") != SCAN_REPORT_SCHEMA:
        raise ValueError("unexpected GitHub Actions scan report schema")
    if report.get("valid") is not True:
        raise ValueError("GitHub Actions scan report must be valid")

    normalized_run_id = _required_text("run_id", run_id)
    ready_runs = report.get("ready_runs")
    if not isinstance(ready_runs, list):
        raise ValueError("scan report ready_runs must be a JSON array")
    matches = [
        dict(item)
        for item in ready_runs
        if isinstance(item, Mapping)
        and str(item.get("run_id", "")).strip() == normalized_run_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one ready run {normalized_run_id}, got {len(matches)}"
        )

    ready_run = matches[0]
    if ready_run.get("status") != "ready":
        raise ValueError("selected run is not ready")
    if ready_run.get("local_execution_started") is not False:
        raise ValueError("selected ready run already claims local execution")
    if ready_run.get("remote_mutation_performed") is not False:
        raise ValueError("selected ready run already claims remote mutation")

    repository = _required_text("repository", ready_run.get("repository"))
    if expected_repository and repository != expected_repository:
        raise ValueError("ready run repository mismatch")
    if report.get("repository") != repository:
        raise ValueError("scan report/ready run repository mismatch")

    artifacts = ready_run.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise ValueError("ready run artifacts must be a JSON object")
    if set(artifacts) != set(_ROLE_FILENAMES):
        raise ValueError("ready run must expose exactly the three expected roles")

    repository_dir = repository.replace("/", "__")
    raw_run_root = dataset_root / "raw" / repository_dir / normalized_run_id
    resolved: dict[str, LocalReadyRunArtifact] = {}
    for role, filename in _ROLE_FILENAMES.items():
        record = artifacts.get(role)
        if not isinstance(record, Mapping):
            raise ValueError(f"ready run role {role} must be an object")
        artifact_id = _required_text(f"{role}.artifact_id", record.get("artifact_id"))
        artifact_name = _required_text(
            f"{role}.artifact_name", record.get("artifact_name")
        )
        record_run_id = _required_text(f"{role}.run_id", record.get("run_id"))
        if record_run_id != normalized_run_id:
            raise ValueError(f"ready run role {role} run_id mismatch")
        availability = _required_text(
            f"{role}.availability", record.get("availability")
        )
        if availability not in {"downloaded", "already_synced"}:
            raise ValueError(f"ready run role {role} is not locally available")

        directory = raw_run_root / artifact_id
        path = _find_exact_file(directory, filename)
        resolved[role] = LocalReadyRunArtifact(
            role=role,
            artifact_id=artifact_id,
            artifact_name=artifact_name,
            directory=directory,
            path=path,
        )

    request_payload = _load_mapping(
        resolved["authoritative_request"].path,
        "authoritative request",
    )
    if request_payload.get("repository") != repository:
        raise ValueError("authoritative request repository mismatch")
    issue_number = request_payload.get("issue_number")
    if isinstance(issue_number, bool) or not isinstance(issue_number, int):
        raise ValueError("authoritative request issue_number must be an integer")
    if issue_number <= 0:
        raise ValueError("authoritative request issue_number must be positive")

    return LocalReadyRunProjectionInput(
        repository=repository,
        run_id=normalized_run_id,
        handoff_ref=_required_text("handoff_ref", ready_run.get("handoff_ref")),
        issue_number=issue_number,
        dataset_root=dataset_root,
        request=resolved["authoritative_request"],
        advisory=resolved["copilot_advisory"],
        manifest=resolved["run_manifest"],
    )


def _load_mapping(path: Path, name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{name} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} is not valid JSON: {path}") from exc
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return dict(value)


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value.strip()


def _find_exact_file(directory: Path, filename: str) -> Path:
    if not directory.is_dir():
        raise ValueError(f"durable artifact directory not found: {directory}")
    matches = tuple(path for path in directory.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise ValueError(
            f"expected one durable {filename} under {directory}, got {len(matches)}"
        )
    return matches[0]
