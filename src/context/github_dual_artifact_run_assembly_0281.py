"""Read-only run-level assembly for correlated GitHub dual artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import re
from typing import Any

from context.github_dual_artifact_source_candidate_intake_0275 import (
    GitHubDualArtifactIntakeCommand,
    run_github_dual_artifact_source_candidate_intake,
)

SCHEMA = "missipy.github.dual_artifact_run_assembly.v1"
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass(frozen=True, slots=True)
class GitHubDualArtifactRunMember:
    """One extracted file associated with one GitHub Actions artifact."""

    artifact_name: str
    filename: str
    content: bytes

    def __post_init__(self) -> None:
        artifact_name = self.artifact_name.strip()
        filename = self.filename.strip()
        if not artifact_name:
            raise ValueError("artifact_name must not be empty")
        if not filename:
            raise ValueError("filename must not be empty")
        if "/" in filename or "\\" in filename or filename in {".", ".."}:
            raise ValueError("filename must be a plain basename")
        if not isinstance(self.content, bytes):
            raise TypeError("content must be bytes")
        object.__setattr__(self, "artifact_name", artifact_name)
        object.__setattr__(self, "filename", filename)

    def to_mapping(self) -> dict[str, object]:
        return {
            "artifact_name": self.artifact_name,
            "filename": self.filename,
            "size_bytes": len(self.content),
            "sha256": hashlib.sha256(self.content).hexdigest(),
        }


@dataclass(frozen=True, slots=True)
class GitHubDualArtifactRunAssemblyPolicy:
    """Names and missing-advisory policy for one dual-artifact workflow run."""

    request_artifact_name: str = "autodoc-authoritative-request"
    request_filename: str = "authoritative_request.json"
    advisory_artifact_name: str = "autodoc-copilot-advisory"
    advisory_filename: str = "copilot_advisory.json"
    manifest_artifact_name: str = "autodoc-dual-artifact-manifest"
    manifest_filename: str = "dual_artifact_manifest.json"
    allow_missing_advisory: bool = True
    ignore_unrecognized_members: bool = True

    def __post_init__(self) -> None:
        names = (
            self.request_artifact_name,
            self.advisory_artifact_name,
            self.manifest_artifact_name,
        )
        filenames = (
            self.request_filename,
            self.advisory_filename,
            self.manifest_filename,
        )
        if any(not value.strip() for value in (*names, *filenames)):
            raise ValueError("artifact names and filenames must not be empty")
        if len(set(names)) != len(names):
            raise ValueError("artifact names must be distinct")
        if len(set(filenames)) != len(filenames):
            raise ValueError("artifact filenames must be distinct")


@dataclass(frozen=True, slots=True)
class GitHubDualArtifactRunAssemblyCommand:
    """Immutable local intention to correlate already-downloaded run members."""

    repository: str
    run_id: str
    members: tuple[GitHubDualArtifactRunMember, ...]
    execute: bool = False

    def __post_init__(self) -> None:
        repository = self.repository.strip()
        run_id = self.run_id.strip()
        if not _REPOSITORY.fullmatch(repository):
            raise ValueError("repository must be owner/name")
        if not run_id:
            raise ValueError("run_id must not be empty")
        if not isinstance(self.members, tuple):
            object.__setattr__(self, "members", tuple(self.members))
        if self.execute:
            raise ValueError("run assembly is read-only and execute must remain false")
        object.__setattr__(self, "repository", repository)
        object.__setattr__(self, "run_id", run_id)


@dataclass(frozen=True, slots=True)
class GitHubDualArtifactRunAssemblyResult:
    """Stable run-level correlation result with locked no-write boundaries."""

    valid: bool
    issues: tuple[str, ...]
    repository: str
    run_id: str
    member_count: int
    recognized_member_count: int
    ignored_member_count: int
    advisory_present: bool
    request_member: Mapping[str, object] = field(default_factory=dict)
    advisory_member: Mapping[str, object] = field(default_factory=dict)
    manifest_member: Mapping[str, object] = field(default_factory=dict)
    intake: Mapping[str, Any] = field(default_factory=dict)
    advisory_payload_retained: bool = False
    advisory_content_authoritative: bool = False
    filesystem_write_performed: bool = False
    scheduler_route_created: bool = False
    sql_write_performed: bool = False
    qdrant_write_performed: bool = False
    github_mutation_performed: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "repository": self.repository,
            "run_id": self.run_id,
            "member_count": self.member_count,
            "recognized_member_count": self.recognized_member_count,
            "ignored_member_count": self.ignored_member_count,
            "advisory_present": self.advisory_present,
            "request_member": dict(self.request_member),
            "advisory_member": dict(self.advisory_member),
            "manifest_member": dict(self.manifest_member),
            "intake": dict(self.intake),
            "advisory_payload_retained": self.advisory_payload_retained,
            "advisory_content_authoritative": False,
            "filesystem_write_performed": False,
            "scheduler_route_created": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
        }


def run_github_dual_artifact_run_assembly(
    command: GitHubDualArtifactRunAssemblyCommand,
    policy: GitHubDualArtifactRunAssemblyPolicy | None = None,
) -> GitHubDualArtifactRunAssemblyResult:
    """Correlate one run and delegate semantic validation to the 0275 intake."""

    effective = policy or GitHubDualArtifactRunAssemblyPolicy()
    slots: dict[str, list[GitHubDualArtifactRunMember]] = {
        "request": [],
        "advisory": [],
        "manifest": [],
    }
    ignored = 0
    issues: list[str] = []

    expected = {
        effective.request_artifact_name: ("request", effective.request_filename),
        effective.advisory_artifact_name: ("advisory", effective.advisory_filename),
        effective.manifest_artifact_name: ("manifest", effective.manifest_filename),
    }

    for member in command.members:
        target = expected.get(member.artifact_name)
        if target is None:
            if effective.ignore_unrecognized_members:
                ignored += 1
                continue
            issues.append(f"unrecognized artifact member: {member.artifact_name}/{member.filename}")
            continue
        slot_name, expected_filename = target
        if member.filename != expected_filename:
            issues.append(
                f"unexpected filename for {member.artifact_name}: {member.filename}"
            )
            continue
        slots[slot_name].append(member)

    for slot_name, members in slots.items():
        if len(members) > 1:
            issues.append(f"duplicate {slot_name} artifact member")

    request = _single(slots["request"])
    advisory = _single(slots["advisory"])
    manifest = _single(slots["manifest"])

    if request is None:
        issues.append("authoritative request artifact member is required")
    if manifest is None:
        issues.append("dual-artifact manifest member is required")
    if advisory is None and not effective.allow_missing_advisory:
        issues.append("Copilot advisory artifact member is required")

    recognized_count = sum(len(values) for values in slots.values())
    if issues or request is None or manifest is None:
        return _result(
            command,
            issues,
            recognized_count,
            ignored,
            request,
            advisory,
            manifest,
        )

    intake = run_github_dual_artifact_source_candidate_intake(
        request.content,
        manifest.content,
        None if advisory is None else advisory.content,
        command=GitHubDualArtifactIntakeCommand(
            allow_missing_advisory=effective.allow_missing_advisory,
        ),
    )
    return GitHubDualArtifactRunAssemblyResult(
        valid=intake.valid,
        issues=intake.issues,
        repository=command.repository,
        run_id=command.run_id,
        member_count=len(command.members),
        recognized_member_count=recognized_count,
        ignored_member_count=ignored,
        advisory_present=advisory is not None,
        request_member=request.to_mapping(),
        advisory_member={} if advisory is None else advisory.to_mapping(),
        manifest_member=manifest.to_mapping(),
        intake=intake.to_mapping(),
        advisory_payload_retained=advisory is not None,
    )


def _single(
    members: list[GitHubDualArtifactRunMember],
) -> GitHubDualArtifactRunMember | None:
    return members[0] if len(members) == 1 else None


def _result(
    command: GitHubDualArtifactRunAssemblyCommand,
    issues: list[str],
    recognized_count: int,
    ignored_count: int,
    request: GitHubDualArtifactRunMember | None,
    advisory: GitHubDualArtifactRunMember | None,
    manifest: GitHubDualArtifactRunMember | None,
) -> GitHubDualArtifactRunAssemblyResult:
    return GitHubDualArtifactRunAssemblyResult(
        valid=False,
        issues=tuple(dict.fromkeys(issues)),
        repository=command.repository,
        run_id=command.run_id,
        member_count=len(command.members),
        recognized_member_count=recognized_count,
        ignored_member_count=ignored_count,
        advisory_present=advisory is not None,
        request_member={} if request is None else request.to_mapping(),
        advisory_member={} if advisory is None else advisory.to_mapping(),
        manifest_member={} if manifest is None else manifest.to_mapping(),
        advisory_payload_retained=advisory is not None,
    )
