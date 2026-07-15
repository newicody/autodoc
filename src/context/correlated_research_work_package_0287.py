"""Correlated research work package for the GitHub-to-laboratory path.

The contract closes already-downloaded GitHub run assembly, source-candidate
intake, optional Copilot advisory and fetched attachment references into one
immutable package. It performs no IO, scheduling, persistence or remote
mutation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any

WORK_PACKAGE_SCHEMA = "missipy.research.correlated_work_package.v1"
BUILD_RESULT_SCHEMA = "missipy.research.correlated_work_package_build.v1"
RUN_ASSEMBLY_SCHEMA = "missipy.github.dual_artifact_run_assembly.v1"
INTAKE_SCHEMA = "missipy.github.dual_artifact_source_candidate_intake.v1"
ATTACHMENT_MANIFEST_SCHEMA = "missipy.github_issue.attachment_manifest.v1"
ATTACHMENT_FETCH_REPORT_SCHEMA = (
    "missipy.github_attachment.reference_fetch_report.v1"
)
REQUEST_SCHEMA = "missipy.github.authoritative_request.v1"
MANIFEST_SCHEMA = "missipy.github.dual_artifact_manifest.v1"
ADVISORY_SCHEMAS = frozenset(
    {
        "missipy.github.copilot_advisory.v1",
        "missipy.github.copilot_advisory.v2",
    }
)

_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CorrelatedResearchWorkPackageError(ValueError):
    """Raised when one input violates a package boundary."""


@dataclass(frozen=True, slots=True)
class ResearchAttachmentReference:
    """Portable reference to one attachment already fetched by the server."""

    url: str
    filename: str
    kind: str
    raw_dataset_ref: str
    sha256: str
    byte_count: int
    content_type: str = ""

    def __post_init__(self) -> None:
        for name in ("url", "filename", "kind", "raw_dataset_ref"):
            _require_text(name, getattr(self, name))
        _require_sha256("sha256", self.sha256)
        if isinstance(self.byte_count, bool) or self.byte_count < 0:
            raise CorrelatedResearchWorkPackageError(
                "byte_count must be a non-negative integer"
            )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": "missipy.research.attachment_reference.v1",
            "url": self.url,
            "filename": self.filename,
            "kind": self.kind,
            "raw_dataset_ref": self.raw_dataset_ref,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "content_type": self.content_type,
            "raw_bytes_embedded": False,
            "local_path_exposed": False,
        }


@dataclass(frozen=True, slots=True)
class CorrelatedResearchWorkPackageCommand:
    """Read-only intention to build one package from correlated mappings."""

    run_assembly: Mapping[str, Any]
    attachment_manifest: Mapping[str, Any] = field(default_factory=dict)
    attachment_fetch_report: Mapping[str, Any] = field(default_factory=dict)
    conversation_ref: str = ""
    return_route_ref: str = ""
    context_generation: int = 0
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    require_advisory: bool = True
    require_fetched_attachments: bool = True
    execute: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.run_assembly, Mapping):
            raise TypeError("run_assembly must be a mapping")
        if not isinstance(self.attachment_manifest, Mapping):
            raise TypeError("attachment_manifest must be a mapping")
        if not isinstance(self.attachment_fetch_report, Mapping):
            raise TypeError("attachment_fetch_report must be a mapping")
        _require_text("conversation_ref", self.conversation_ref)
        _require_text("return_route_ref", self.return_route_ref)
        if isinstance(self.context_generation, bool) or self.context_generation < 0:
            raise CorrelatedResearchWorkPackageError(
                "context_generation must be a non-negative integer"
            )
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
            raise CorrelatedResearchWorkPackageError(
                "work-package construction is read-only and execute must remain false"
            )


@dataclass(frozen=True, slots=True)
class CorrelatedResearchWorkPackage:
    """Immutable package ready for a later Scheduler-owned laboratory route."""

    work_package_ref: str
    repository: str
    run_id: str
    issue_number: int
    issue_url: str
    origin_frame_id: str
    ticket_revision_id: str
    source_candidate_ref: str
    conversation_ref: str
    return_route_ref: str
    context_generation: int
    authoritative_request: Mapping[str, Any]
    correlation_manifest: Mapping[str, Any]
    copilot_advisory: Mapping[str, Any] = field(default_factory=dict)
    attachments: tuple[ResearchAttachmentReference, ...] = ()
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text("work_package_ref", self.work_package_ref)
        if not self.work_package_ref.startswith("research-work-package:"):
            raise CorrelatedResearchWorkPackageError(
                "work_package_ref must start with research-work-package:"
            )
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise CorrelatedResearchWorkPackageError(
                "repository must be owner/name"
            )
        for name in (
            "run_id",
            "issue_url",
            "origin_frame_id",
            "ticket_revision_id",
            "source_candidate_ref",
            "conversation_ref",
            "return_route_ref",
        ):
            _require_text(name, getattr(self, name))
        if isinstance(self.issue_number, bool) or self.issue_number <= 0:
            raise CorrelatedResearchWorkPackageError(
                "issue_number must be > 0"
            )
        object.__setattr__(
            self,
            "authoritative_request",
            _freeze_mapping(self.authoritative_request),
        )
        object.__setattr__(
            self,
            "correlation_manifest",
            _freeze_mapping(self.correlation_manifest),
        )
        object.__setattr__(
            self,
            "copilot_advisory",
            _freeze_mapping(self.copilot_advisory),
        )
        object.__setattr__(self, "attachments", tuple(self.attachments))
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

    @property
    def advisory_present(self) -> bool:
        return bool(self.copilot_advisory)

    def to_mapping(self) -> dict[str, Any]:
        request = dict(self.authoritative_request)
        advisory = dict(self.copilot_advisory)
        manifest = dict(self.correlation_manifest)
        attachment_mappings = [item.to_mapping() for item in self.attachments]
        return {
            "schema": WORK_PACKAGE_SCHEMA,
            "work_package_ref": self.work_package_ref,
            "repository": self.repository,
            "run_id": self.run_id,
            "source_issue": {
                "number": self.issue_number,
                "url": self.issue_url,
            },
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "source_candidate_ref": self.source_candidate_ref,
            "conversation_ref": self.conversation_ref,
            "return_route_ref": self.return_route_ref,
            "context_generation": self.context_generation,
            "authoritative_request": request,
            "correlation_manifest": manifest,
            "copilot_advisory": advisory,
            "advisory_present": self.advisory_present,
            "advisory_schema": advisory.get("schema", ""),
            "attachments": attachment_mappings,
            "attachment_refs": [
                item.raw_dataset_ref for item in self.attachments
            ],
            "context_refs": list(self.context_refs),
            "evidence_refs": list(self.evidence_refs),
            "request_authoritative": True,
            "advisory_used_as_hint_only": True,
            "attachment_bytes_embedded": False,
            "ready_for_laboratory_route": True,
            "scheduler_route_created": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
        }


@dataclass(frozen=True, slots=True)
class CorrelatedResearchWorkPackageBuildResult:
    valid: bool
    issues: tuple[str, ...]
    work_package: Mapping[str, Any] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": BUILD_RESULT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "work_package": dict(self.work_package),
            "request_authoritative": True,
            "advisory_used_as_hint_only": True,
            "scheduler_route_created": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
        }


def build_correlated_research_work_package(
    command: CorrelatedResearchWorkPackageCommand,
) -> CorrelatedResearchWorkPackageBuildResult:
    """Validate all correlations and build one deterministic work package."""

    issues: list[str] = []
    run = _mapping(command.run_assembly)
    _expect(run, "schema", RUN_ASSEMBLY_SCHEMA, issues)
    _expect(run, "valid", True, issues)
    _expect(run, "advisory_content_authoritative", False, issues)
    for flag in (
        "filesystem_write_performed",
        "scheduler_route_created",
        "sql_write_performed",
        "qdrant_write_performed",
        "github_mutation_performed",
    ):
        _expect(run, flag, False, issues)

    repository = _text_value(run, "repository", issues)
    run_id = _text_value(run, "run_id", issues)
    if repository and not _REPOSITORY_RE.fullmatch(repository):
        issues.append("run assembly repository must be owner/name")

    intake = _mapping(run.get("intake"))
    _expect(intake, "schema", INTAKE_SCHEMA, issues)
    _expect(intake, "valid", True, issues)
    _expect(intake, "request_authoritative", True, issues)
    _expect(intake, "advisory_used_as_hint_only", True, issues)
    for flag in (
        "scheduler_route_created",
        "sql_write_performed",
        "qdrant_write_performed",
        "github_mutation_performed",
    ):
        _expect(intake, flag, False, issues)

    request = _mapping(intake.get("request"))
    advisory = _mapping(intake.get("advisory"))
    manifest = _mapping(intake.get("manifest"))
    source_candidate = _mapping(intake.get("source_candidate"))

    _expect(request, "schema", REQUEST_SCHEMA, issues)
    _expect(request, "authoritative", True, issues)
    _expect(request, "advisory_content_embedded", False, issues)
    _expect(request, "remote_mutation_requested", False, issues)
    _expect(manifest, "schema", MANIFEST_SCHEMA, issues)
    _expect(manifest, "request_is_authority", True, issues)
    _expect(manifest, "advisory_is_authority", False, issues)

    request_repository = _text_value(request, "repository", issues)
    issue_number = request.get("issue_number")
    issue_url = _text_value(request, "issue_url", issues)
    origin_frame_id = _text_value(request, "origin_frame_id", issues)
    ticket_revision_id = _text_value(request, "ticket_revision_id", issues)
    request_artifact_ref = _text_value(request, "artifact_ref", issues)
    source_candidate_ref = _text_value(
        source_candidate,
        "candidate_id",
        issues,
    )

    if request_repository and repository and request_repository != repository:
        issues.append("request repository does not match run assembly")
    if isinstance(issue_number, bool) or not isinstance(issue_number, int):
        issues.append("request issue_number must be an integer")
    elif issue_number <= 0:
        issues.append("request issue_number must be > 0")

    _same(
        "manifest origin_frame_id",
        manifest.get("origin_frame_id"),
        origin_frame_id,
        issues,
    )
    _same(
        "manifest ticket_revision_id",
        manifest.get("ticket_revision_id"),
        ticket_revision_id,
        issues,
    )
    _same(
        "manifest request_artifact_ref",
        manifest.get("request_artifact_ref"),
        request_artifact_ref,
        issues,
    )
    _require_sha256_mapping("manifest request_sha256", manifest, "request_sha256", issues)

    advisory_present = bool(advisory)
    if command.require_advisory and not advisory_present:
        issues.append("Copilot advisory is required by work-package command")
    if advisory_present:
        schema = advisory.get("schema")
        if schema not in ADVISORY_SCHEMAS:
            issues.append("unsupported Copilot advisory schema")
        _expect(advisory, "trusted", False, issues)
        _expect(advisory, "usable_as_hint", True, issues)
        _expect(advisory, "usable_as_authority", False, issues)
        _same(
            "advisory origin_frame_id",
            advisory.get("origin_frame_id"),
            origin_frame_id,
            issues,
        )
        _same(
            "advisory ticket_revision_id",
            advisory.get("ticket_revision_id"),
            ticket_revision_id,
            issues,
        )
        _same(
            "advisory request_artifact_ref",
            advisory.get("request_artifact_ref"),
            request_artifact_ref,
            issues,
        )
        _same(
            "manifest advisory_artifact_ref",
            manifest.get("advisory_artifact_ref"),
            advisory.get("artifact_ref"),
            issues,
        )
        _require_sha256_mapping(
            "manifest advisory_sha256",
            manifest,
            "advisory_sha256",
            issues,
        )
    elif manifest.get("advisory_artifact_ref") is not None:
        issues.append("manifest references an advisory missing from intake")

    attachments = _build_attachment_references(
        command,
        repository=request_repository,
        run_id=run_id,
        issue_number=issue_number if isinstance(issue_number, int) else 0,
        issue_url=issue_url,
        origin_frame_id=origin_frame_id,
        ticket_revision_id=ticket_revision_id,
        issues=issues,
    )

    if issues:
        return CorrelatedResearchWorkPackageBuildResult(
            valid=False,
            issues=tuple(dict.fromkeys(issues)),
        )

    stable_payload = {
        "repository": repository,
        "run_id": run_id,
        "issue_number": issue_number,
        "origin_frame_id": origin_frame_id,
        "ticket_revision_id": ticket_revision_id,
        "source_candidate_ref": source_candidate_ref,
        "request_artifact_ref": request_artifact_ref,
        "request_sha256": manifest["request_sha256"],
        "advisory_artifact_ref": advisory.get("artifact_ref", ""),
        "advisory_sha256": manifest.get("advisory_sha256", ""),
        "attachment_sha256": [item.sha256 for item in attachments],
        "conversation_ref": command.conversation_ref,
        "return_route_ref": command.return_route_ref,
        "context_generation": command.context_generation,
        "context_refs": list(command.context_refs),
        "evidence_refs": list(command.evidence_refs),
    }
    digest = hashlib.sha256(_canonical_json(stable_payload)).hexdigest()
    package = CorrelatedResearchWorkPackage(
        work_package_ref=f"research-work-package:{digest[:24]}",
        repository=repository,
        run_id=run_id,
        issue_number=issue_number,
        issue_url=issue_url,
        origin_frame_id=origin_frame_id,
        ticket_revision_id=ticket_revision_id,
        source_candidate_ref=source_candidate_ref,
        conversation_ref=command.conversation_ref,
        return_route_ref=command.return_route_ref,
        context_generation=command.context_generation,
        authoritative_request=request,
        correlation_manifest=manifest,
        copilot_advisory=advisory,
        attachments=attachments,
        context_refs=command.context_refs,
        evidence_refs=command.evidence_refs,
    )
    return CorrelatedResearchWorkPackageBuildResult(
        valid=True,
        issues=(),
        work_package=package.to_mapping(),
    )


def _build_attachment_references(
    command: CorrelatedResearchWorkPackageCommand,
    *,
    repository: str,
    run_id: str,
    issue_number: int,
    issue_url: str,
    origin_frame_id: str,
    ticket_revision_id: str,
    issues: list[str],
) -> tuple[ResearchAttachmentReference, ...]:
    manifest = _mapping(command.attachment_manifest)
    report = _mapping(command.attachment_fetch_report)
    if not manifest:
        if report:
            issues.append("attachment fetch report requires an attachment manifest")
        return ()

    _expect(manifest, "schema", ATTACHMENT_MANIFEST_SCHEMA, issues)
    _same("attachment repository", manifest.get("repository"), repository, issues)
    issue = _mapping(manifest.get("issue"))
    _same("attachment issue number", issue.get("number"), issue_number, issues)
    _same("attachment issue url", issue.get("url"), issue_url, issues)
    _same(
        "attachment origin_frame_id",
        manifest.get("origin_frame_id"),
        origin_frame_id,
        issues,
    )
    _same(
        "attachment ticket_revision_id",
        manifest.get("ticket_revision_id"),
        ticket_revision_id,
        issues,
    )
    raw_attachments = manifest.get("attachments", ())
    if not _is_sequence(raw_attachments):
        issues.append("attachment manifest attachments must be a sequence")
        return ()
    manifest_items = tuple(_mapping(item) for item in raw_attachments)
    if not manifest_items:
        if report:
            _validate_empty_fetch_report(
                report,
                repository=repository,
                run_id=run_id,
                origin_frame_id=origin_frame_id,
                ticket_revision_id=ticket_revision_id,
                issues=issues,
            )
        return ()
    if not report:
        if command.require_fetched_attachments:
            issues.append("referenced attachments require a fetch report")
        return ()

    _expect(report, "schema", ATTACHMENT_FETCH_REPORT_SCHEMA, issues)
    _same("fetch repository", report.get("repository"), repository, issues)
    _same("fetch run_id", report.get("run_id"), run_id, issues)
    _same(
        "fetch origin_frame_id",
        report.get("origin_frame_id"),
        origin_frame_id,
        issues,
    )
    _same(
        "fetch ticket_revision_id",
        report.get("ticket_revision_id"),
        ticket_revision_id,
        issues,
    )
    raw_records = report.get("records", ())
    if not _is_sequence(raw_records):
        issues.append("attachment fetch records must be a sequence")
        return ()
    records = tuple(_mapping(item) for item in raw_records)
    by_url: dict[str, Mapping[str, Any]] = {}
    for record in records:
        reference = _mapping(record.get("reference"))
        url = str(reference.get("url", "")).strip()
        if not url:
            issues.append("fetched attachment reference url must not be empty")
            continue
        if url in by_url:
            issues.append(f"duplicate fetched attachment url: {url}")
        by_url[url] = record

    built: list[ResearchAttachmentReference] = []
    manifest_urls: set[str] = set()
    for item in manifest_items:
        url = str(item.get("url", "")).strip()
        if not url:
            issues.append("attachment manifest url must not be empty")
            continue
        if url in manifest_urls:
            issues.append(f"duplicate attachment manifest url: {url}")
            continue
        manifest_urls.add(url)
        record = by_url.get(url)
        if record is None:
            if command.require_fetched_attachments:
                issues.append(f"attachment was not fetched: {url}")
            continue
        if record.get("status") != "fetched":
            issues.append(f"attachment fetch did not complete: {url}")
            continue
        reference = _mapping(record.get("reference"))
        filename = str(reference.get("filename") or item.get("filename") or "")
        kind = str(reference.get("kind") or item.get("kind") or "")
        raw_dataset_ref = str(record.get("raw_dataset_ref", "")).strip()
        sha256 = str(record.get("sha256", "")).strip()
        byte_count = record.get("byte_count")
        if not raw_dataset_ref:
            issues.append(f"attachment raw_dataset_ref is missing: {url}")
            continue
        if not _SHA256_RE.fullmatch(sha256):
            issues.append(f"attachment sha256 is invalid: {url}")
            continue
        if isinstance(byte_count, bool) or not isinstance(byte_count, int):
            issues.append(f"attachment byte_count is invalid: {url}")
            continue
        expected = str(reference.get("expected_sha256", "")).strip()
        if expected and expected != sha256:
            issues.append(f"attachment expected_sha256 mismatch: {url}")
            continue
        built.append(
            ResearchAttachmentReference(
                url=url,
                filename=filename,
                kind=kind,
                raw_dataset_ref=raw_dataset_ref,
                sha256=sha256,
                byte_count=byte_count,
                content_type=str(reference.get("content_type", "")),
            )
        )
    extra_urls = sorted(set(by_url) - manifest_urls)
    if extra_urls:
        issues.append(
            "fetch report contains attachments absent from manifest: "
            + ", ".join(extra_urls)
        )
    return tuple(built)


def _validate_empty_fetch_report(
    report: Mapping[str, Any],
    *,
    repository: str,
    run_id: str,
    origin_frame_id: str,
    ticket_revision_id: str,
    issues: list[str],
) -> None:
    _expect(report, "schema", ATTACHMENT_FETCH_REPORT_SCHEMA, issues)
    _same("fetch repository", report.get("repository"), repository, issues)
    _same("fetch run_id", report.get("run_id"), run_id, issues)
    _same(
        "fetch origin_frame_id",
        report.get("origin_frame_id"),
        origin_frame_id,
        issues,
    )
    _same(
        "fetch ticket_revision_id",
        report.get("ticket_revision_id"),
        ticket_revision_id,
        issues,
    )
    records = report.get("records", ())
    if not _is_sequence(records) or records:
        issues.append("empty attachment manifest requires an empty fetch report")


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


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _expect(
    mapping: Mapping[str, Any],
    key: str,
    expected: object,
    issues: list[str],
) -> None:
    if mapping.get(key) != expected:
        issues.append(f"{key} must be {expected!r}")


def _same(
    name: str,
    actual: object,
    expected: object,
    issues: list[str],
) -> None:
    if actual != expected:
        issues.append(f"{name} mismatch")


def _text_value(
    mapping: Mapping[str, Any],
    key: str,
    issues: list[str],
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{key} must be a non-empty string")
        return ""
    return value.strip()


def _require_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CorrelatedResearchWorkPackageError(
            f"{name} must be a non-empty string"
        )
    return value.strip()


def _require_sha256(name: str, value: object) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise CorrelatedResearchWorkPackageError(f"{name} must be sha256")
    return value


def _require_sha256_mapping(
    name: str,
    mapping: Mapping[str, Any],
    key: str,
    issues: list[str],
) -> None:
    value = mapping.get(key)
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        issues.append(f"{name} must be sha256")


def _unique_texts(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise CorrelatedResearchWorkPackageError(
            f"{name} must be a sequence of strings"
        )
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_text(name, value))
    return tuple(dict.fromkeys(normalized))


def _is_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _freeze_mapping(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(_copy_json_value(mapping))


def _copy_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _copy_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_copy_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
