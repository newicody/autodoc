"""Correlation contract for one imported Actions run and its r14 preview.

This module does not fetch artifacts, create a Scheduler or mutate GitHub.  It
validates that one already imported workflow run, one completed r14 result and
one r15-r1 remote publication preview describe the same immutable plan.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRealBackendAttestation,
)

LOVE_IMPORTED_ACTIONS_RUN_PREVIEW_COMMAND_SCHEMA = (
    "missipy.love.imported_actions_run_preview_command.v1"
)
LOVE_IMPORTED_ACTIONS_RUN_PREVIEW_RESULT_SCHEMA = (
    "missipy.love.imported_actions_run_preview_result.v1"
)
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_ARTIFACT_FILES = {
    "autodoc-authoritative-request": "authoritative_request.json",
    "autodoc-copilot-advisory": "copilot_advisory.json",
    "autodoc-dual-artifact-manifest": "dual_artifact_manifest.json",
}


class LoveImportedActionsRunPreviewError(RuntimeError):
    """Raised when imported-run correlation fails closed."""


@dataclass(frozen=True, slots=True)
class GitHubActionsArtifactIdentity:
    """Stable identity of one downloaded Actions artifact."""

    artifact_id: int
    artifact_name: str
    filename: str
    archive_size_in_bytes: int
    content_size_in_bytes: int
    content_digest: str
    created_at: str
    expired: bool = False

    def __post_init__(self) -> None:
        if self.artifact_id <= 0:
            raise LoveImportedActionsRunPreviewError(
                "artifact_id must be positive"
            )
        expected = _EXPECTED_ARTIFACT_FILES.get(self.artifact_name)
        if expected is None:
            raise LoveImportedActionsRunPreviewError(
                f"unexpected artifact name: {self.artifact_name}"
            )
        if self.filename != expected:
            raise LoveImportedActionsRunPreviewError(
                f"unexpected filename for {self.artifact_name}: {self.filename}"
            )
        if self.archive_size_in_bytes < 0:
            raise LoveImportedActionsRunPreviewError(
                "archive_size_in_bytes must be non-negative"
            )
        if self.content_size_in_bytes < 0:
            raise LoveImportedActionsRunPreviewError(
                "content_size_in_bytes must be non-negative"
            )
        if not _SHA256_RE.fullmatch(self.content_digest):
            raise LoveImportedActionsRunPreviewError(
                "content_digest must be a SHA-256 hexadecimal digest"
            )
        if not self.created_at.strip():
            raise LoveImportedActionsRunPreviewError(
                "artifact created_at must be non-empty"
            )
        if self.expired:
            raise LoveImportedActionsRunPreviewError(
                f"artifact is expired: {self.artifact_name}"
            )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_name": self.artifact_name,
            "filename": self.filename,
            "archive_size_in_bytes": self.archive_size_in_bytes,
            "content_size_in_bytes": self.content_size_in_bytes,
            "content_digest": self.content_digest,
            "created_at": self.created_at,
            "expired": False,
        }


@dataclass(frozen=True, slots=True)
class LoveImportedActionsRunPreviewCommand:
    """Immutable correlation intention after local r14 execution."""

    schema: str
    repository: str
    run_id: str
    workflow_name: str
    workflow_conclusion: str
    artifacts: tuple[GitHubActionsArtifactIdentity, ...]
    runtime_attestation: ImportedActionsRealBackendAttestation

    def __post_init__(self) -> None:
        if self.schema != LOVE_IMPORTED_ACTIONS_RUN_PREVIEW_COMMAND_SCHEMA:
            raise LoveImportedActionsRunPreviewError(
                "unsupported imported Actions preview command schema"
            )
        if not _REPOSITORY_RE.fullmatch(self.repository):
            raise LoveImportedActionsRunPreviewError(
                "repository must use owner/name"
            )
        if not self.run_id.strip():
            raise LoveImportedActionsRunPreviewError("run_id must be non-empty")
        if not self.workflow_name.strip():
            raise LoveImportedActionsRunPreviewError(
                "workflow_name must be non-empty"
            )
        if self.workflow_conclusion != "success":
            raise LoveImportedActionsRunPreviewError(
                "workflow run must be completed successfully"
            )
        if not isinstance(self.artifacts, tuple):
            object.__setattr__(self, "artifacts", tuple(self.artifacts))
        names = tuple(item.artifact_name for item in self.artifacts)
        if len(names) != 3 or set(names) != set(_EXPECTED_ARTIFACT_FILES):
            raise LoveImportedActionsRunPreviewError(
                "exactly the three correlated Actions artifacts are required"
            )
        if len({item.artifact_id for item in self.artifacts}) != 3:
            raise LoveImportedActionsRunPreviewError(
                "artifact ids must be distinct"
            )
        if not isinstance(
            self.runtime_attestation,
            ImportedActionsRealBackendAttestation,
        ):
            raise LoveImportedActionsRunPreviewError(
                "runtime_attestation must prove existing real backends"
            )


@dataclass(frozen=True, slots=True)
class LoveImportedActionsRunPreviewResult:
    """One compatible r14 JSON enriched with imported-run preview evidence."""

    schema: str
    repository: str
    run_id: str
    workflow_name: str
    artifacts: tuple[GitHubActionsArtifactIdentity, ...]
    runtime_attestation: ImportedActionsRealBackendAttestation
    proof_digest: str
    plan_digest: str
    r14_result: Mapping[str, Any]
    publication_preview: Mapping[str, Any]
    valid: bool
    issues: tuple[str, ...]
    remote_mutation_performed: bool = False

    def to_mapping(self) -> dict[str, Any]:
        # Preserve the r14 top-level publication_plan so the existing r15-r1
        # parser can consume the generated file directly.
        payload = dict(self.r14_result)
        payload["_r15_import"] = {
            "schema": self.schema,
            "repository": self.repository,
            "run_id": self.run_id,
            "workflow_name": self.workflow_name,
            "artifact_ids": [item.artifact_id for item in self.artifacts],
            "artifacts": [item.to_mapping() for item in self.artifacts],
            "proof_digest": self.proof_digest,
            "plan_digest": self.plan_digest,
            "runtime_attestation": self.runtime_attestation.to_mapping(),
            "live_path_status": "real-backend-preview",
            "live_path_uses_real_backend": True,
            "preview_required": True,
            "remote_mutation_performed": False,
            "valid": self.valid,
            "issues": list(self.issues),
        }
        payload["remote_publication_preview"] = dict(
            self.publication_preview
        )
        return payload


def correlate_imported_actions_run_preview(
    command: LoveImportedActionsRunPreviewCommand,
    *,
    r14_result: Mapping[str, Any],
    publication_preview: Mapping[str, Any],
) -> LoveImportedActionsRunPreviewResult:
    """Validate exact run, proof and plan correlation without mutation."""

    issues: list[str] = []
    run_assembly = _mapping(r14_result.get("run_assembly"), "run_assembly")
    publication_plan = _mapping(
        r14_result.get("publication_plan"),
        "publication_plan",
    )
    proof_digest = str(r14_result.get("proof_digest", ""))
    plan_digest = str(publication_plan.get("plan_digest", ""))
    synthesis_result = _mapping(
        r14_result.get("synthesis_result"),
        "synthesis_result",
    )
    projection_receipts = _mapping_sequence(
        synthesis_result.get("projection_receipts"),
        "synthesis_result.projection_receipts",
    )

    if str(run_assembly.get("repository", "")) != command.repository:
        issues.append("r14 repository differs from imported Actions run")
    if str(run_assembly.get("run_id", "")) != command.run_id:
        issues.append("r14 run_id differs from imported Actions run")
    if not _SHA256_RE.fullmatch(proof_digest):
        issues.append("r14 proof_digest is missing or invalid")
    if not _SHA256_RE.fullmatch(plan_digest):
        issues.append("r13 plan_digest is missing or invalid")
    if publication_preview.get("mode") != "preview":
        issues.append("r15-r1 result must remain in preview mode")
    if publication_preview.get("plan_digest") != plan_digest:
        issues.append("preview plan_digest differs from r14 publication plan")
    if publication_preview.get("remote_mutation_performed") is not False:
        issues.append("preview unexpectedly reports a remote mutation")
    if publication_preview.get("valid") is not True:
        issues.append("remote publication preview is not valid")
    if len(projection_receipts) != 2:
        issues.append("r14 must contain two real projection receipts")
    for receipt in projection_receipts:
        projection = _mapping(
            receipt.get("projection"),
            "projection receipt metadata",
        )
        if receipt.get("openvino_e5_used") is not True:
            issues.append("r14 projection receipt lacks real OpenVINO/E5 proof")
        if receipt.get("qdrant_write_performed") is not True:
            issues.append("r14 projection receipt lacks real Qdrant write proof")
        if int(projection.get("dimension", 0)) != 384:
            issues.append("r14 projection receipt is not E5 dimension 384")
        if projection.get("normalized") is not True:
            issues.append("r14 projection receipt is not normalized")
        if (
            str(projection.get("collection_name", ""))
            != command.runtime_attestation.qdrant_collection
        ):
            issues.append(
                "r14 projection collection differs from runtime attestation"
            )

    valid = not issues
    return LoveImportedActionsRunPreviewResult(
        schema=LOVE_IMPORTED_ACTIONS_RUN_PREVIEW_RESULT_SCHEMA,
        repository=command.repository,
        run_id=command.run_id,
        workflow_name=command.workflow_name,
        artifacts=command.artifacts,
        runtime_attestation=command.runtime_attestation,
        proof_digest=proof_digest,
        plan_digest=plan_digest,
        r14_result=dict(r14_result),
        publication_preview=dict(publication_preview),
        valid=valid,
        issues=tuple(issues),
    )


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LoveImportedActionsRunPreviewError(
            f"{name} must be a mapping"
        )
    return value


def _mapping_sequence(
    value: object,
    name: str,
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(
        value,
        (str, bytes, bytearray),
    ):
        raise LoveImportedActionsRunPreviewError(
            f"{name} must be a sequence"
        )
    if not all(isinstance(item, Mapping) for item in value):
        raise LoveImportedActionsRunPreviewError(
            f"{name} must contain mappings"
        )
    return tuple(value)


__all__ = [
    "GitHubActionsArtifactIdentity",
    "LOVE_IMPORTED_ACTIONS_RUN_PREVIEW_COMMAND_SCHEMA",
    "LOVE_IMPORTED_ACTIONS_RUN_PREVIEW_RESULT_SCHEMA",
    "LoveImportedActionsRunPreviewCommand",
    "LoveImportedActionsRunPreviewError",
    "LoveImportedActionsRunPreviewResult",
    "correlate_imported_actions_run_preview",
]
