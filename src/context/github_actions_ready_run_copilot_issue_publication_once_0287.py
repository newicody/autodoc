"""Pure selection and path contract for local Copilot Issue publication.

The GitHub Actions workflow remains a read-only artifact producer.  This module
selects strict three-artifact ``ready_runs`` from one existing scan report and
maps their artifact ids to the durable local raw dataset.  It performs no IO,
GitHub mutation, SQL write, Qdrant write, Scheduler call, or laboratory run.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import re
from pathlib import Path
from typing import Any

SCAN_SCHEMA = "missipy.github_actions.artifact_scan_once_live.v1"
STATE_SCHEMA = "missipy.github_actions.ready_run_copilot_issue_publication_state.v1"
RESULT_SCHEMA = "missipy.github_actions.ready_run_copilot_issue_publication_once.v1"
EXPECTED_ROLES = (
    "authoritative_request",
    "copilot_advisory",
    "run_manifest",
)
EXPECTED_FILENAMES = {
    "authoritative_request": "authoritative_request.json",
    "copilot_advisory": "copilot_advisory.json",
    "run_manifest": "dual_artifact_manifest.json",
}
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_RUN_ID_RE = re.compile(r"^[1-9][0-9]*$")
_ARTIFACT_ID_RE = re.compile(r"^[1-9][0-9]*$")


@dataclass(frozen=True, slots=True)
class ReadyRunPublicationCandidate:
    repository: str
    run_id: str
    handoff_ref: str
    artifact_ids: Mapping[str, str]
    publication_key: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "run_id": self.run_id,
            "handoff_ref": self.handoff_ref,
            "artifact_ids": dict(self.artifact_ids),
            "publication_key": self.publication_key,
        }


def select_ready_run_publication_candidates(
    scan_report: Mapping[str, Any],
    *,
    completed_keys: Sequence[str] = (),
    requested_run_ids: Sequence[str] = (),
    max_runs: int = 10,
    include_completed: bool = False,
) -> tuple[ReadyRunPublicationCandidate, ...]:
    """Return newest strict ready-run candidates, bounded and deterministic."""
    if max_runs <= 0:
        raise ValueError("max_runs must be > 0")
    if scan_report.get("schema") != SCAN_SCHEMA:
        raise ValueError("unexpected scan report schema")
    if scan_report.get("kind") != "result":
        raise ValueError("scan report must be a result")
    if scan_report.get("valid") is not True:
        raise ValueError("scan report must be valid")

    ready_runs = scan_report.get("ready_runs")
    if not isinstance(ready_runs, list):
        raise ValueError("ready_runs must be a JSON array")

    requested = {str(item).strip() for item in requested_run_ids if str(item).strip()}
    completed = {str(item).strip() for item in completed_keys if str(item).strip()}
    candidates: list[ReadyRunPublicationCandidate] = []

    for item in ready_runs:
        candidate = parse_ready_run_publication_candidate(item)
        if requested and candidate.run_id not in requested:
            continue
        if not include_completed and candidate.publication_key in completed:
            continue
        candidates.append(candidate)

    candidates.sort(key=lambda item: (int(item.run_id), item.run_id), reverse=True)
    selected = tuple(candidates[:max_runs])
    if requested:
        found = {item.run_id for item in selected}
        missing = requested - found
        if missing:
            raise ValueError(
                "requested ready run not selectable: " + ", ".join(sorted(missing))
            )
    return selected


def parse_ready_run_publication_candidate(
    value: object,
) -> ReadyRunPublicationCandidate:
    if not isinstance(value, Mapping):
        raise ValueError("each ready_run must be a JSON object")
    repository = _required_repository(value.get("repository"))
    run_id = _required_identifier("run_id", value.get("run_id"), _RUN_ID_RE)
    if value.get("status") != "ready":
        raise ValueError(f"run {run_id} is not ready")
    if value.get("local_execution_started") is not False:
        raise ValueError(f"run {run_id} already claims local execution")
    if value.get("remote_mutation_performed") is not False:
        raise ValueError(f"run {run_id} already claims remote mutation")

    artifacts = value.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise ValueError(f"run {run_id} artifacts must be an object")
    roles = tuple(sorted(str(role) for role in artifacts))
    if roles != tuple(sorted(EXPECTED_ROLES)):
        raise ValueError(f"run {run_id} must expose exactly the three expected roles")

    artifact_ids: dict[str, str] = {}
    for role in EXPECTED_ROLES:
        artifact = artifacts.get(role)
        if not isinstance(artifact, Mapping):
            raise ValueError(f"run {run_id} role {role} must be an object")
        artifact_run_id = _required_identifier(
            f"{role}.run_id", artifact.get("run_id"), _RUN_ID_RE
        )
        if artifact_run_id != run_id:
            raise ValueError(f"run {run_id} role {role} run_id mismatch")
        availability = str(artifact.get("availability", "")).strip()
        if availability not in {"downloaded", "already_synced"}:
            raise ValueError(f"run {run_id} role {role} is not locally available")
        artifact_ids[role] = _required_identifier(
            f"{role}.artifact_id", artifact.get("artifact_id"), _ARTIFACT_ID_RE
        )

    handoff_ref = str(value.get("handoff_ref", "")).strip()
    if not handoff_ref:
        raise ValueError(f"run {run_id} handoff_ref must be non-empty")
    return ReadyRunPublicationCandidate(
        repository=repository,
        run_id=run_id,
        handoff_ref=handoff_ref,
        artifact_ids=artifact_ids,
        publication_key=build_publication_key(repository, run_id, artifact_ids),
    )


def build_publication_key(
    repository: str,
    run_id: str,
    artifact_ids: Mapping[str, str],
) -> str:
    repository = _required_repository(repository)
    run_id = _required_identifier("run_id", run_id, _RUN_ID_RE)
    payload = [repository, run_id]
    for role in EXPECTED_ROLES:
        payload.extend(
            (
                role,
                _required_identifier(
                    f"{role}.artifact_id", artifact_ids.get(role), _ARTIFACT_ID_RE
                ),
            )
        )
    digest = hashlib.sha256("\0".join(payload).encode("utf-8")).hexdigest()
    return f"ready-run-copilot-issue-publication:{digest}"


def durable_raw_member_paths(
    dataset_root: Path,
    candidate: ReadyRunPublicationCandidate,
) -> dict[str, Path]:
    """Map one candidate to deterministic paths below the durable raw root."""
    repository_slug = candidate.repository.replace("/", "__")
    raw_root = Path(dataset_root) / "raw" / repository_slug / candidate.run_id
    return {
        role: raw_root / candidate.artifact_ids[role] / EXPECTED_FILENAMES[role]
        for role in EXPECTED_ROLES
    }


def completed_publication_keys(state: Mapping[str, Any]) -> tuple[str, ...]:
    if not state:
        return ()
    if state.get("schema") != STATE_SCHEMA:
        raise ValueError("unexpected publication state schema")
    completed = state.get("completed")
    if not isinstance(completed, Mapping):
        raise ValueError("publication state completed must be an object")
    return tuple(str(key) for key in completed)


def _required_repository(value: object) -> str:
    text = str(value or "").strip()
    if not _REPOSITORY_RE.fullmatch(text):
        raise ValueError("repository must use owner/name")
    return text


def _required_identifier(name: str, value: object, pattern: re.Pattern[str]) -> str:
    text = str(value or "").strip()
    if not pattern.fullmatch(text):
        raise ValueError(f"{name} must be a positive decimal identifier")
    return text
