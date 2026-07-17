"""Human-readable identities for GitHub and server artifacts.

The visible name explains the source Issue and artifact kind.  Immutable
artifact references and content digests remain the correlation authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import unicodedata
from typing import Any, Mapping

HUMAN_READABLE_ARTIFACT_IDENTITY_SCHEMA = (
    "autodoc.human_readable_artifact_identity.v1"
)
HUMAN_READABLE_ARTIFACT_IDENTITY_BUNDLE_SCHEMA = (
    "autodoc.human_readable_artifact_identity_bundle.v1"
)

_KIND_CONTRACTS: dict[str, dict[str, object]] = {
    "authoritative_request": {
        "display_prefix": "Demande autoritative",
        "actions_suffix": "authoritative-request-v1",
        "legacy_actions_name": "autodoc-authoritative-request",
        "filename": "authoritative_request.json",
        "content_summary": (
            "Demande autoritative issue du ticket GitHub, utilisée comme source "
            "de vérité du cycle"
        ),
        "content_sections": (
            "title",
            "body",
            "labels",
            "requested_status",
            "request_mode",
        ),
    },
    "copilot_advisory": {
        "display_prefix": "Premier avis Copilot",
        "actions_suffix": "copilot-advisory-v2",
        "legacy_actions_name": "autodoc-copilot-advisory",
        "filename": "copilot_advisory.json",
        "content_summary": (
            "Avis consultatif sur l’objectif, le résultat attendu, les contraintes "
            "et les critères de réussite"
        ),
        "content_sections": (
            "concrete_objective",
            "expected_result",
            "provided_constraints",
            "success_criteria",
        ),
    },
    "run_manifest": {
        "display_prefix": "Manifest du cycle",
        "actions_suffix": "run-manifest-v1",
        "legacy_actions_name": "autodoc-dual-artifact-manifest",
        "filename": "dual_artifact_manifest.json",
        "content_summary": (
            "Index de corrélation des artefacts, références et empreintes du run"
        ),
        "content_sections": (
            "request_artifact_ref",
            "request_sha256",
            "advisory_artifact_ref",
            "advisory_sha256",
        ),
    },
}


class HumanReadableArtifactIdentityError(ValueError):
    """Raised when source artifacts cannot receive a trustworthy identity."""


@dataclass(frozen=True, slots=True)
class HumanReadableArtifactIdentity:
    schema: str
    artifact_kind: str
    issue_number: int
    source_title: str
    title_slug: str
    display_title: str
    actions_name: str
    legacy_actions_name: str
    filename: str
    artifact_ref: str
    content_summary: str
    content_sections: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "artifact_kind": self.artifact_kind,
            "issue_number": self.issue_number,
            "source_title": self.source_title,
            "title_slug": self.title_slug,
            "display_title": self.display_title,
            "actions_name": self.actions_name,
            "legacy_actions_name": self.legacy_actions_name,
            "filename": self.filename,
            "artifact_ref": self.artifact_ref,
            "content_summary": self.content_summary,
            "content_sections": list(self.content_sections),
        }


@dataclass(frozen=True, slots=True)
class HumanReadableArtifactIdentityBundle:
    schema: str
    repository: str
    issue_number: int
    source_title: str
    source_ref: str
    workflow_run_id: str
    identities: tuple[HumanReadableArtifactIdentity, ...]
    bundle_digest: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "repository": self.repository,
            "issue_number": self.issue_number,
            "source_title": self.source_title,
            "source_ref": self.source_ref,
            "workflow_run_id": self.workflow_run_id,
            "identities": [item.to_mapping() for item in self.identities],
            "bundle_digest": self.bundle_digest,
        }

    def identity(self, artifact_kind: str) -> HumanReadableArtifactIdentity:
        matches = tuple(
            item for item in self.identities if item.artifact_kind == artifact_kind
        )
        if len(matches) != 1:
            raise HumanReadableArtifactIdentityError(
                f"expected exactly one identity for {artifact_kind}"
            )
        return matches[0]


def slugify_issue_title(title: str, *, issue_number: int, limit: int = 64) -> str:
    """Return a stable ASCII slug suitable for an Actions artifact name."""
    if issue_number <= 0:
        raise HumanReadableArtifactIdentityError("issue_number must be positive")
    normalized = unicodedata.normalize("NFKD", str(title).strip())
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")
    slug = re.sub(r"-+", "-", slug)
    if not slug:
        slug = f"issue-{issue_number}"
    if len(slug) > limit:
        slug = slug[:limit].rstrip("-")
    return slug or f"issue-{issue_number}"


def human_readable_suffix_for_legacy_name(legacy_name: str) -> str:
    """Return the strict suffix accepted for a new readable Actions name."""
    for contract in _KIND_CONTRACTS.values():
        if contract["legacy_actions_name"] == legacy_name:
            return "--" + str(contract["actions_suffix"])
    raise HumanReadableArtifactIdentityError(
        f"unknown legacy Actions artifact name: {legacy_name}"
    )


def matches_actions_artifact_name(actual_name: str, legacy_name: str) -> bool:
    """Accept one historical exact name or one canonical readable name."""
    actual_name = str(actual_name).strip()
    if actual_name == legacy_name:
        return True
    suffix = human_readable_suffix_for_legacy_name(legacy_name)
    return actual_name.startswith("autodoc-i") and actual_name.endswith(suffix)


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise HumanReadableArtifactIdentityError(f"{name} must be a mapping")
    return value


def _non_empty(value: object, name: str) -> str:
    rendered = str(value or "").strip()
    if not rendered:
        raise HumanReadableArtifactIdentityError(f"{name} must be non-empty")
    return rendered


def _identity(
    *,
    artifact_kind: str,
    issue_number: int,
    source_title: str,
    title_slug: str,
    artifact_ref: str,
) -> HumanReadableArtifactIdentity:
    contract = _KIND_CONTRACTS[artifact_kind]
    actions_suffix = str(contract["actions_suffix"])
    return HumanReadableArtifactIdentity(
        schema=HUMAN_READABLE_ARTIFACT_IDENTITY_SCHEMA,
        artifact_kind=artifact_kind,
        issue_number=issue_number,
        source_title=source_title,
        title_slug=title_slug,
        display_title=f"{contract['display_prefix']} — {source_title}",
        actions_name=(
            f"autodoc-i{issue_number}-{title_slug}--{actions_suffix}"
        ),
        legacy_actions_name=str(contract["legacy_actions_name"]),
        filename=str(contract["filename"]),
        artifact_ref=artifact_ref,
        content_summary=str(contract["content_summary"]),
        content_sections=tuple(str(item) for item in contract["content_sections"]),
    )


def build_human_readable_artifact_identity_bundle(
    *,
    repository: str,
    workflow_run_id: str,
    issue: Mapping[str, Any],
    request: Mapping[str, Any],
    advisory: Mapping[str, Any] | None,
    manifest: Mapping[str, Any],
) -> HumanReadableArtifactIdentityBundle:
    """Build readable names without changing the underlying artifact schemas."""
    repository = _non_empty(repository, "repository")
    workflow_run_id = _non_empty(workflow_run_id, "workflow_run_id")
    issue = _mapping(issue, "issue")
    request = _mapping(request, "request")
    manifest = _mapping(manifest, "manifest")

    issue_number = int(issue.get("number") or request.get("issue_number") or 0)
    if issue_number <= 0:
        raise HumanReadableArtifactIdentityError("Issue number must be positive")
    if int(request.get("issue_number") or 0) != issue_number:
        raise HumanReadableArtifactIdentityError("Issue/request number mismatch")
    if str(request.get("repository", "")).strip() != repository:
        raise HumanReadableArtifactIdentityError("request repository mismatch")

    source_title = _non_empty(issue.get("title") or request.get("title"), "title")
    request_ref = _non_empty(request.get("artifact_ref"), "request artifact_ref")
    manifest_ref = _non_empty(manifest.get("manifest_ref"), "manifest_ref")
    if manifest.get("request_artifact_ref") != request_ref:
        raise HumanReadableArtifactIdentityError("manifest/request correlation mismatch")

    title_slug = slugify_issue_title(source_title, issue_number=issue_number)
    identities = [
        _identity(
            artifact_kind="authoritative_request",
            issue_number=issue_number,
            source_title=source_title,
            title_slug=title_slug,
            artifact_ref=request_ref,
        )
    ]

    if advisory is not None:
        advisory = _mapping(advisory, "advisory")
        advisory_ref = _non_empty(advisory.get("artifact_ref"), "advisory artifact_ref")
        if advisory.get("request_artifact_ref") != request_ref:
            raise HumanReadableArtifactIdentityError(
                "advisory/request correlation mismatch"
            )
        if manifest.get("advisory_artifact_ref") != advisory_ref:
            raise HumanReadableArtifactIdentityError(
                "manifest/advisory correlation mismatch"
            )
        identities.append(
            _identity(
                artifact_kind="copilot_advisory",
                issue_number=issue_number,
                source_title=source_title,
                title_slug=title_slug,
                artifact_ref=advisory_ref,
            )
        )
    elif manifest.get("advisory_artifact_ref") is not None:
        raise HumanReadableArtifactIdentityError(
            "manifest declares an advisory but no advisory was supplied"
        )

    identities.append(
        _identity(
            artifact_kind="run_manifest",
            issue_number=issue_number,
            source_title=source_title,
            title_slug=title_slug,
            artifact_ref=manifest_ref,
        )
    )
    source_ref = f"github-frame:{repository}/issues/{issue_number}"
    digest_payload = {
        "repository": repository,
        "issue_number": issue_number,
        "source_title": source_title,
        "source_ref": source_ref,
        "workflow_run_id": workflow_run_id,
        "identities": [item.to_mapping() for item in identities],
    }
    bundle_digest = "sha256:" + hashlib.sha256(
        json.dumps(
            digest_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return HumanReadableArtifactIdentityBundle(
        schema=HUMAN_READABLE_ARTIFACT_IDENTITY_BUNDLE_SCHEMA,
        repository=repository,
        issue_number=issue_number,
        source_title=source_title,
        source_ref=source_ref,
        workflow_run_id=workflow_run_id,
        identities=tuple(identities),
        bundle_digest=bundle_digest,
    )
