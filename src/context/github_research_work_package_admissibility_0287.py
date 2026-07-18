"""Pure admissibility gate for fetched GitHub research work packages.

This module sits after the existing dual-artifact assembly, semantic intake and
``CorrelatedResearchWorkPackage`` construction.  It does not reopen artifact
files and does not duplicate their digest validation.  It only decides whether
an already correlated package may be handed to a later Scheduler-owned route.

No SQL, Qdrant, GitHub mutation, Scheduler dispatch or laboratory execution is
performed here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

from context.correlated_research_work_package_0287 import WORK_PACKAGE_SCHEMA

ADMISSIBILITY_SCHEMA = "missipy.github.research_work_package_admissibility.v1"
ROUTE_CANDIDATE_SCHEMA = "missipy.github.research_laboratory_route_candidate.v1"
REQUEST_SCHEMA = "missipy.github.authoritative_request.v1"
MANIFEST_SCHEMA = "missipy.github.dual_artifact_manifest.v1"


@dataclass(frozen=True, slots=True)
class GitHubResearchWorkPackageAdmissibilityPolicy:
    """Explicit policy for the repository dedicated to managed research."""

    allowed_repository: str = "newicody/projects"
    allowed_requested_statuses: tuple[str, ...] = ("Recherche",)
    allowed_request_modes: tuple[str, ...] = ("initial", "continuation")
    require_copilot_advisory: bool = True
    require_parent_for_continuation: bool = True

    def __post_init__(self) -> None:
        if not self.allowed_repository.strip():
            raise ValueError("allowed_repository must not be empty")
        if not self.allowed_requested_statuses:
            raise ValueError("allowed_requested_statuses must not be empty")
        if not self.allowed_request_modes:
            raise ValueError("allowed_request_modes must not be empty")


@dataclass(frozen=True, slots=True)
class GitHubResearchWorkPackageAdmissibilityCommand:
    """Read-only request to evaluate one correlated work package."""

    work_package: Mapping[str, Any]
    execute: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.work_package, Mapping):
            raise TypeError("work_package must be a mapping")
        if self.execute:
            raise ValueError(
                "admissibility evaluation is read-only and execute must remain false"
            )


@dataclass(frozen=True, slots=True)
class GitHubResearchWorkPackageAdmissibilityResult:
    """Stable decision without dispatching the Scheduler."""

    admissible: bool
    status: str
    issues: tuple[str, ...]
    repository: str = ""
    run_id: str = ""
    issue_number: int = 0
    requested_status: str = ""
    request_mode: str = ""
    parent_event_ref: str = ""
    route_candidate: Mapping[str, Any] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": ADMISSIBILITY_SCHEMA,
            "valid": self.admissible,
            "admissible": self.admissible,
            "status": self.status,
            "issues": list(self.issues),
            "repository": self.repository,
            "run_id": self.run_id,
            "issue_number": self.issue_number,
            "requested_status": self.requested_status,
            "request_mode": self.request_mode,
            "parent_event_ref": self.parent_event_ref,
            "route_candidate": dict(self.route_candidate),
            "existing_work_package_reused": True,
            "artifact_files_reopened": False,
            "artifact_digest_validation_duplicated": False,
            "request_authoritative": True,
            "advisory_used_as_hint_only": True,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
            "scheduler_command_created": False,
            "scheduler_dispatch_started": False,
            "laboratory_execution_started": False,
        }


def evaluate_github_research_work_package_admissibility(
    command: GitHubResearchWorkPackageAdmissibilityCommand,
    policy: GitHubResearchWorkPackageAdmissibilityPolicy | None = None,
) -> GitHubResearchWorkPackageAdmissibilityResult:
    """Validate research intent and return a deterministic route candidate."""

    effective = policy or GitHubResearchWorkPackageAdmissibilityPolicy()
    package = command.work_package
    issues: list[str] = []

    _expect(package, "schema", WORK_PACKAGE_SCHEMA, issues)
    _expect(package, "ready_for_laboratory_route", True, issues)
    _expect(package, "request_authoritative", True, issues)
    _expect(package, "advisory_used_as_hint_only", True, issues)
    for key in (
        "scheduler_route_created",
        "sql_write_performed",
        "qdrant_write_performed",
        "github_mutation_performed",
    ):
        _expect(package, key, False, issues)

    repository = _text(package.get("repository"))
    run_id = _text(package.get("run_id"))
    work_package_ref = _text(package.get("work_package_ref"))
    if repository != effective.allowed_repository:
        issues.append(
            "repository must be the dedicated research repository "
            f"{effective.allowed_repository}"
        )
    if not run_id:
        issues.append("run_id must not be empty")
    if not work_package_ref.startswith("research-work-package:"):
        issues.append("work_package_ref must identify a correlated research package")

    source_issue = _mapping(package.get("source_issue"))
    issue_number = source_issue.get("number")
    if isinstance(issue_number, bool) or not isinstance(issue_number, int):
        issues.append("source issue number must be an integer")
        normalized_issue_number = 0
    elif issue_number <= 0:
        issues.append("source issue number must be > 0")
        normalized_issue_number = 0
    else:
        normalized_issue_number = issue_number

    request = _mapping(package.get("authoritative_request"))
    manifest = _mapping(package.get("correlation_manifest"))
    advisory = _mapping(package.get("copilot_advisory"))
    _expect(request, "schema", REQUEST_SCHEMA, issues)
    _expect(request, "authoritative", True, issues)
    _expect(request, "advisory_content_embedded", False, issues)
    _expect(request, "remote_mutation_requested", False, issues)
    _expect(manifest, "schema", MANIFEST_SCHEMA, issues)
    _expect(manifest, "request_is_authority", True, issues)
    _expect(manifest, "advisory_is_authority", False, issues)

    if _text(request.get("repository")) != repository:
        issues.append("authoritative request repository mismatch")
    if request.get("issue_number") != normalized_issue_number:
        issues.append("authoritative request issue number mismatch")

    metadata = _mapping(request.get("metadata"))
    requested_status = _text(metadata.get("requested_status"))
    request_mode = _text(metadata.get("request_mode"))
    parent_event_ref = _text(metadata.get("parent_event_ref"))

    if requested_status not in effective.allowed_requested_statuses:
        issues.append(
            "requested_status must explicitly identify an admissible research request"
        )
    if request_mode not in effective.allowed_request_modes:
        issues.append("request_mode is not recognized by the research route")
    elif request_mode == "initial" and parent_event_ref:
        issues.append("an initial research request must not carry parent_event_ref")
    elif (
        request_mode == "continuation"
        and effective.require_parent_for_continuation
        and not parent_event_ref
    ):
        issues.append("a continuation research request requires parent_event_ref")

    advisory_present = bool(advisory) and package.get("advisory_present") is True
    if effective.require_copilot_advisory and not advisory_present:
        issues.append("the correlated Copilot advisory is required")
    if advisory_present:
        _expect(advisory, "trusted", False, issues)
        _expect(advisory, "usable_as_hint", True, issues)
        _expect(advisory, "usable_as_authority", False, issues)

    if issues:
        return GitHubResearchWorkPackageAdmissibilityResult(
            admissible=False,
            status="inadmissible",
            issues=tuple(dict.fromkeys(issues)),
            repository=repository,
            run_id=run_id,
            issue_number=normalized_issue_number,
            requested_status=requested_status,
            request_mode=request_mode,
            parent_event_ref=parent_event_ref,
        )

    candidate_payload = {
        "work_package_ref": work_package_ref,
        "repository": repository,
        "run_id": run_id,
        "issue_number": normalized_issue_number,
        "requested_status": requested_status,
        "request_mode": request_mode,
        "parent_event_ref": parent_event_ref,
        "conversation_ref": _text(package.get("conversation_ref")),
        "return_route_ref": _text(package.get("return_route_ref")),
        "context_generation": package.get("context_generation", 0),
        "context_refs": _texts(package.get("context_refs")),
        "evidence_refs": _texts(package.get("evidence_refs")),
    }
    digest = hashlib.sha256(_canonical_json(candidate_payload)).hexdigest()
    route_candidate = {
        "schema": ROUTE_CANDIDATE_SCHEMA,
        "route_candidate_ref": f"research-route-candidate:{digest[:24]}",
        **candidate_payload,
        "admissibility_digest": digest,
        "scheduler_command_created": False,
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
    }
    return GitHubResearchWorkPackageAdmissibilityResult(
        admissible=True,
        status="admissible",
        issues=(),
        repository=repository,
        run_id=run_id,
        issue_number=normalized_issue_number,
        requested_status=requested_status,
        request_mode=request_mode,
        parent_event_ref=parent_event_ref,
        route_candidate=route_candidate,
    )


def _expect(
    mapping: Mapping[str, Any],
    key: str,
    expected: object,
    issues: list[str],
) -> None:
    if mapping.get(key) != expected:
        issues.append(f"{key} must be {expected!r}")


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _texts(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return list(dict.fromkeys(_text(item) for item in value if _text(item)))


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            dict(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
