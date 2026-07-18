"""Assemble one fetched ready_run and evaluate research admissibility.

The existing GitHub Actions scan already correlates the three locally available
artifacts by repository and run.  This module consumes that handoff plus the
already-read artifact bytes, delegates semantic validation to the existing
dual-artifact assembly, builds the existing correlated research work package,
then delegates the research decision to the r16-r6 admissibility gate.

It performs no filesystem IO, SQL or Qdrant write, GitHub mutation, Scheduler
dispatch, or laboratory execution.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from context.correlated_research_work_package_0287 import (
    CorrelatedResearchWorkPackageCommand,
    build_correlated_research_work_package,
)
from context.github_dual_artifact_run_assembly_0281 import (
    GitHubDualArtifactRunAssemblyCommand,
    GitHubDualArtifactRunAssemblyPolicy,
    GitHubDualArtifactRunMember,
    run_github_dual_artifact_run_assembly,
)
from context.github_research_work_package_admissibility_0287 import (
    GitHubResearchWorkPackageAdmissibilityCommand,
    evaluate_github_research_work_package_admissibility,
)

SCHEMA = "missipy.github.ready_run_research_admissibility_assembly.v1"
_READY_RUN_STATUS = "ready"
_EXPECTED_ROLES = (
    "authoritative_request",
    "copilot_advisory",
    "run_manifest",
)
_ROLE_SPECIFICATIONS = {
    "authoritative_request": (
        "autodoc-authoritative-request",
        "authoritative_request.json",
    ),
    "copilot_advisory": (
        "autodoc-copilot-advisory",
        "copilot_advisory.json",
    ),
    "run_manifest": (
        "autodoc-dual-artifact-manifest",
        "dual_artifact_manifest.json",
    ),
}


@dataclass(frozen=True, slots=True)
class GitHubReadyRunArtifactContent:
    """Bytes loaded by a filesystem adapter for one ready_run role."""

    role: str
    content: bytes
    artifact_id: str = ""
    source_artifact_name: str = ""

    def __post_init__(self) -> None:
        role = self.role.strip()
        if role not in _ROLE_SPECIFICATIONS:
            raise ValueError(f"unsupported artifact role: {role or '<empty>'}")
        if not isinstance(self.content, bytes):
            raise TypeError("content must be bytes")
        if not self.content:
            raise ValueError("content must not be empty")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "artifact_id", self.artifact_id.strip())
        object.__setattr__(
            self,
            "source_artifact_name",
            self.source_artifact_name.strip(),
        )


@dataclass(frozen=True, slots=True)
class GitHubReadyRunResearchAdmissibilityCommand:
    """Read-only request to close one ready_run into an admissibility result."""

    ready_run: Mapping[str, Any]
    artifact_contents: tuple[GitHubReadyRunArtifactContent, ...]
    conversation_ref: str = ""
    return_route_ref: str = ""
    context_generation: int = 0
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    execute: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.ready_run, Mapping):
            raise TypeError("ready_run must be a mapping")
        if not isinstance(self.artifact_contents, tuple):
            object.__setattr__(
                self,
                "artifact_contents",
                tuple(self.artifact_contents),
            )
        if isinstance(self.context_generation, bool) or self.context_generation < 0:
            raise ValueError("context_generation must be a non-negative integer")
        object.__setattr__(
            self,
            "context_refs",
            _unique_texts("context_refs", self.context_refs),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _unique_texts("evidence_refs", self.evidence_refs),
        )
        if self.execute:
            raise ValueError(
                "ready_run assembly is read-only and execute must remain false"
            )


@dataclass(frozen=True, slots=True)
class GitHubReadyRunResearchAdmissibilityResult:
    """Stable assembly result without creating a Scheduler command."""

    valid: bool
    admissible: bool
    status: str
    issues: tuple[str, ...]
    repository: str = ""
    run_id: str = ""
    handoff_ref: str = ""
    run_assembly: Mapping[str, Any] = field(default_factory=dict)
    work_package_build: Mapping[str, Any] = field(default_factory=dict)
    admissibility: Mapping[str, Any] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "valid": self.valid,
            "admissible": self.admissible,
            "status": self.status,
            "issues": list(self.issues),
            "repository": self.repository,
            "run_id": self.run_id,
            "handoff_ref": self.handoff_ref,
            "run_assembly": dict(self.run_assembly),
            "work_package_build": dict(self.work_package_build),
            "admissibility": dict(self.admissibility),
            "existing_ready_run_reused": True,
            "existing_dual_artifact_assembly_reused": True,
            "existing_correlated_work_package_reused": True,
            "existing_admissibility_gate_reused": True,
            "request_authoritative": True,
            "advisory_used_as_hint_only": True,
            "filesystem_write_performed": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
            "scheduler_command_created": False,
            "scheduler_dispatch_started": False,
            "laboratory_execution_started": False,
        }


def assemble_ready_run_and_evaluate_research_admissibility(
    command: GitHubReadyRunResearchAdmissibilityCommand,
) -> GitHubReadyRunResearchAdmissibilityResult:
    """Reuse the existing correlation chain and return one route decision."""

    ready_run = command.ready_run
    issues: list[str] = []
    repository = _text(ready_run.get("repository"))
    run_id = _text(ready_run.get("run_id"))
    handoff_ref = _text(ready_run.get("handoff_ref"))

    if ready_run.get("status") != _READY_RUN_STATUS:
        issues.append("ready_run status must be 'ready'")
    if not repository:
        issues.append("ready_run repository must not be empty")
    if not run_id:
        issues.append("ready_run run_id must not be empty")
    expected_handoff = (
        f"github-actions-ready-run:{repository.replace('/', '-')}:{run_id}"
        if repository and run_id
        else ""
    )
    if handoff_ref != expected_handoff:
        issues.append("ready_run handoff_ref mismatch")
    if ready_run.get("artifact_count") != len(_EXPECTED_ROLES):
        issues.append("ready_run artifact_count must be 3")
    if ready_run.get("local_execution_started") is not False:
        issues.append("ready_run must not have started local execution")
    if ready_run.get("remote_mutation_performed") is not False:
        issues.append("ready_run must not have performed remote mutation")

    artifacts = _mapping(ready_run.get("artifacts"))
    if set(artifacts) != set(_EXPECTED_ROLES):
        issues.append("ready_run must contain exactly the three expected roles")

    contents_by_role: dict[str, GitHubReadyRunArtifactContent] = {}
    for content in command.artifact_contents:
        if content.role in contents_by_role:
            issues.append(f"duplicate loaded artifact role: {content.role}")
            continue
        contents_by_role[content.role] = content
    missing_contents = sorted(set(_EXPECTED_ROLES) - set(contents_by_role))
    if missing_contents:
        issues.append(
            "loaded artifact content missing roles: " + ", ".join(missing_contents)
        )
    extra_contents = sorted(set(contents_by_role) - set(_EXPECTED_ROLES))
    if extra_contents:
        issues.append(
            "loaded artifact content has unknown roles: " + ", ".join(extra_contents)
        )

    for role in _EXPECTED_ROLES:
        record = _mapping(artifacts.get(role))
        content = contents_by_role.get(role)
        if not record:
            continue
        if _text(record.get("run_id")) != run_id:
            issues.append(f"{role} run_id mismatch")
        artifact_id = _text(record.get("artifact_id"))
        artifact_name = _text(record.get("artifact_name"))
        availability = _text(record.get("availability"))
        if not artifact_id:
            issues.append(f"{role} artifact_id must not be empty")
        if not artifact_name:
            issues.append(f"{role} artifact_name must not be empty")
        if availability not in {"downloaded", "already_synced"}:
            issues.append(f"{role} artifact is not locally available")
        if content is not None:
            if content.artifact_id and content.artifact_id != artifact_id:
                issues.append(f"{role} loaded artifact_id mismatch")
            if (
                content.source_artifact_name
                and content.source_artifact_name != artifact_name
            ):
                issues.append(f"{role} loaded artifact_name mismatch")

    if issues:
        return _result(
            valid=False,
            admissible=False,
            status="ready-run-invalid",
            issues=issues,
            repository=repository,
            run_id=run_id,
            handoff_ref=handoff_ref,
        )

    members = tuple(
        GitHubDualArtifactRunMember(
            artifact_name=_ROLE_SPECIFICATIONS[role][0],
            filename=_ROLE_SPECIFICATIONS[role][1],
            content=contents_by_role[role].content,
        )
        for role in _EXPECTED_ROLES
    )
    assembly = run_github_dual_artifact_run_assembly(
        GitHubDualArtifactRunAssemblyCommand(
            repository=repository,
            run_id=run_id,
            members=members,
        ),
        GitHubDualArtifactRunAssemblyPolicy(allow_missing_advisory=False),
    )
    assembly_mapping = assembly.to_mapping()
    if not assembly.valid:
        return _result(
            valid=False,
            admissible=False,
            status="run-assembly-invalid",
            issues=list(assembly.issues),
            repository=repository,
            run_id=run_id,
            handoff_ref=handoff_ref,
            run_assembly=assembly_mapping,
        )

    intake = _mapping(assembly_mapping.get("intake"))
    request = _mapping(intake.get("request"))
    issue_number = request.get("issue_number")
    if isinstance(issue_number, bool) or not isinstance(issue_number, int):
        return _result(
            valid=False,
            admissible=False,
            status="run-assembly-invalid",
            issues=["assembled request issue_number must be an integer"],
            repository=repository,
            run_id=run_id,
            handoff_ref=handoff_ref,
            run_assembly=assembly_mapping,
        )

    repository_slug = repository.replace("/", "-")
    conversation_ref = (
        command.conversation_ref.strip()
        or f"github-research-conversation:{repository_slug}:{issue_number}:{run_id}"
    )
    return_route_ref = (
        command.return_route_ref.strip()
        or f"github-issue-return:{repository_slug}:{issue_number}"
    )
    context_refs = tuple(
        dict.fromkeys((handoff_ref, *command.context_refs))
    )
    evidence_refs = tuple(
        dict.fromkeys(
            (
                *command.evidence_refs,
                *(
                    f"github-actions-artifact:{repository_slug}:{run_id}:"
                    f"{_text(_mapping(artifacts[role]).get('artifact_id'))}"
                    for role in _EXPECTED_ROLES
                ),
            )
        )
    )

    package_build = build_correlated_research_work_package(
        CorrelatedResearchWorkPackageCommand(
            run_assembly=assembly_mapping,
            conversation_ref=conversation_ref,
            return_route_ref=return_route_ref,
            context_generation=command.context_generation,
            context_refs=context_refs,
            evidence_refs=evidence_refs,
            require_advisory=True,
            require_fetched_attachments=False,
        )
    )
    package_mapping = package_build.to_mapping()
    if not package_build.valid:
        return _result(
            valid=False,
            admissible=False,
            status="work-package-invalid",
            issues=list(package_build.issues),
            repository=repository,
            run_id=run_id,
            handoff_ref=handoff_ref,
            run_assembly=assembly_mapping,
            work_package_build=package_mapping,
        )

    admissibility = evaluate_github_research_work_package_admissibility(
        GitHubResearchWorkPackageAdmissibilityCommand(
            work_package=package_mapping["work_package"],
        )
    )
    admissibility_mapping = admissibility.to_mapping()
    return _result(
        valid=True,
        admissible=admissibility.admissible,
        status="admissible" if admissibility.admissible else "inadmissible",
        issues=list(admissibility.issues),
        repository=repository,
        run_id=run_id,
        handoff_ref=handoff_ref,
        run_assembly=assembly_mapping,
        work_package_build=package_mapping,
        admissibility=admissibility_mapping,
    )


def _result(
    *,
    valid: bool,
    admissible: bool,
    status: str,
    issues: Sequence[str],
    repository: str,
    run_id: str,
    handoff_ref: str,
    run_assembly: Mapping[str, Any] | None = None,
    work_package_build: Mapping[str, Any] | None = None,
    admissibility: Mapping[str, Any] | None = None,
) -> GitHubReadyRunResearchAdmissibilityResult:
    return GitHubReadyRunResearchAdmissibilityResult(
        valid=valid,
        admissible=admissible,
        status=status,
        issues=tuple(dict.fromkeys(str(issue) for issue in issues if str(issue))),
        repository=repository,
        run_id=run_id,
        handoff_ref=handoff_ref,
        run_assembly=dict(run_assembly or {}),
        work_package_build=dict(work_package_build or {}),
        admissibility=dict(admissibility or {}),
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _unique_texts(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence of strings")
    normalized: list[str] = []
    for value in values:
        text = _text(value)
        if not text:
            raise ValueError(f"{name} must contain non-empty strings")
        normalized.append(text)
    return tuple(dict.fromkeys(normalized))
