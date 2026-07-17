"""Readable, correlated Copilot v2 publication composition.

This module is pure.  It enriches the existing v2 preview with the human-readable
artifact identity, prepares a readable Issue-comment plan from the existing v2
renderer, and binds the Issue and ProjectV2 plans under one confirmation digest.
Network access remains in the thin tool adapter.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

READABLE_COPILOT_PUBLICATION_IDENTITY_SCHEMA = (
    "autodoc.readable_copilot_publication_identity.v1"
)
READABLE_COPILOT_ISSUE_PLAN_SCHEMA = (
    "autodoc.readable_copilot_issue_publication_plan.v1"
)
READABLE_COPILOT_COMBINED_PLAN_SCHEMA = (
    "autodoc.readable_copilot_combined_publication_plan.v1"
)
IDENTITY_BUNDLE_SCHEMA = "autodoc.human_readable_artifact_identity_bundle.v1"
PREVIEW_SCHEMA = "missipy.github.copilot_advisory_publication_preview.v2"


class ReadableCopilotPublicationError(ValueError):
    """Raised when readable and technical identities do not correlate."""


@dataclass(frozen=True, slots=True)
class ReadableCopilotPublicationIdentity:
    schema: str
    repository: str
    issue_number: int
    source_title: str
    source_ref: str
    workflow_run_id: str
    workflow_run_url: str
    display_title: str
    actions_name: str
    technical_artifact_ref: str
    identity_bundle_digest: str
    project_artifact_value: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "repository": self.repository,
            "issue_number": self.issue_number,
            "source_title": self.source_title,
            "source_ref": self.source_ref,
            "workflow_run_id": self.workflow_run_id,
            "workflow_run_url": self.workflow_run_url,
            "display_title": self.display_title,
            "actions_name": self.actions_name,
            "technical_artifact_ref": self.technical_artifact_ref,
            "identity_bundle_digest": self.identity_bundle_digest,
            "project_artifact_value": self.project_artifact_value,
        }


@dataclass(frozen=True, slots=True)
class ReadableCopilotIssuePublicationPlan:
    schema: str
    valid: bool
    action: str
    issues: tuple[str, ...]
    marker: str
    body: str
    body_sha256: str
    plan_digest: str
    existing_comment_id: int | None = None
    existing_comment_url: str = ""

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "action": self.action,
            "issues": list(self.issues),
            "marker": self.marker,
            "body": self.body,
            "body_sha256": self.body_sha256,
            "plan_digest": self.plan_digest,
            "existing_comment_id": self.existing_comment_id,
            "existing_comment_url": self.existing_comment_url,
            "request_authoritative": True,
            "advisory_is_authority": False,
            "collision_guarded": True,
            "idempotent_replay": self.action == "replay",
        }


@dataclass(frozen=True, slots=True)
class ReadableCopilotCombinedPublicationPlan:
    schema: str
    valid: bool
    issues: tuple[str, ...]
    issue_action: str
    project_action: str
    issue_plan_digest: str
    project_plan_digest: str
    identity_bundle_digest: str
    plan_digest: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "issue_action": self.issue_action,
            "project_action": self.project_action,
            "issue_plan_digest": self.issue_plan_digest,
            "project_plan_digest": self.project_plan_digest,
            "identity_bundle_digest": self.identity_bundle_digest,
            "plan_digest": self.plan_digest,
            "operator_decision_required": True,
            "preview_required": True,
            "request_authoritative": True,
            "advisory_is_authority": False,
            "remote_mutation_allowed": False,
            "mutation_performed": False,
        }


def resolve_readable_copilot_publication_identity(
    preview: Mapping[str, Any],
    identity_bundle: Mapping[str, Any],
    *,
    artifact_limit: int = 256,
) -> ReadableCopilotPublicationIdentity:
    """Correlate a v2 preview with exactly one readable Copilot identity."""
    if preview.get("schema") != PREVIEW_SCHEMA:
        raise ReadableCopilotPublicationError("unexpected publication preview schema")
    if identity_bundle.get("schema") != IDENTITY_BUNDLE_SCHEMA:
        raise ReadableCopilotPublicationError("unexpected artifact identity schema")

    repository = _text(preview.get("repository"), "repository")
    issue_number = _positive_int(preview.get("issue_number"), "issue_number")
    if identity_bundle.get("repository") != repository:
        raise ReadableCopilotPublicationError("identity repository mismatch")
    if identity_bundle.get("issue_number") != issue_number:
        raise ReadableCopilotPublicationError("identity Issue mismatch")

    source_ref = _text(identity_bundle.get("source_ref"), "source_ref")
    if preview.get("source_candidate_ref") != source_ref:
        raise ReadableCopilotPublicationError("identity source reference mismatch")
    workflow_run_id = _text(
        identity_bundle.get("workflow_run_id"), "workflow_run_id"
    )
    if preview.get("workflow_run_ref") != f"github-actions-run:{workflow_run_id}":
        raise ReadableCopilotPublicationError("identity workflow run mismatch")

    identities = identity_bundle.get("identities")
    if not isinstance(identities, Sequence) or isinstance(
        identities, (str, bytes, bytearray)
    ):
        raise ReadableCopilotPublicationError("identities must be an array")
    matches = tuple(
        item
        for item in identities
        if isinstance(item, Mapping)
        and item.get("artifact_kind") == "copilot_advisory"
    )
    if len(matches) != 1:
        raise ReadableCopilotPublicationError(
            "expected exactly one readable Copilot identity"
        )
    advisory = matches[0]
    technical_ref = _text(
        preview.get("advisory_artifact_ref"), "advisory_artifact_ref"
    )
    if advisory.get("artifact_ref") != technical_ref:
        raise ReadableCopilotPublicationError("advisory artifact reference mismatch")

    display_title = _text(advisory.get("display_title"), "display_title")
    actions_name = _text(advisory.get("actions_name"), "actions_name")
    if not actions_name.endswith("--copilot-advisory-v2"):
        raise ReadableCopilotPublicationError("unexpected readable advisory name")
    source_title = _text(identity_bundle.get("source_title"), "source_title")
    bundle_digest = _sha256_ref(
        identity_bundle.get("bundle_digest"), "bundle_digest"
    )
    run_url = f"https://github.com/{repository}/actions/runs/{workflow_run_id}"
    project_value = render_project_artifact_value(
        display_title=display_title,
        workflow_run_url=run_url,
        technical_artifact_ref=technical_ref,
        limit=artifact_limit,
    )
    return ReadableCopilotPublicationIdentity(
        schema=READABLE_COPILOT_PUBLICATION_IDENTITY_SCHEMA,
        repository=repository,
        issue_number=issue_number,
        source_title=source_title,
        source_ref=source_ref,
        workflow_run_id=workflow_run_id,
        workflow_run_url=run_url,
        display_title=display_title,
        actions_name=actions_name,
        technical_artifact_ref=technical_ref,
        identity_bundle_digest=bundle_digest,
        project_artifact_value=project_value,
    )


def render_project_artifact_value(
    *,
    display_title: str,
    workflow_run_url: str,
    technical_artifact_ref: str,
    limit: int = 256,
) -> str:
    """Render a bounded locator that is readable and still technically traceable."""
    if limit < 128:
        raise ReadableCopilotPublicationError("artifact field limit must be >= 128")
    title = _text(display_title, "display_title")
    run_url = _text(workflow_run_url, "workflow_run_url")
    artifact_ref = _text(technical_artifact_ref, "technical_artifact_ref")
    suffix = f" | {run_url} | {artifact_ref}"
    available = limit - len(suffix)
    if available < 12:
        raise ReadableCopilotPublicationError("artifact locator cannot fit the limit")
    if len(title) > available:
        title = title[: max(1, available - 1)].rstrip() + "…"
    value = title + suffix
    if len(value) > limit:
        raise AssertionError("bounded artifact locator exceeded its limit")
    return value


def enrich_projectv2_preview(
    preview: Mapping[str, Any],
    identity: ReadableCopilotPublicationIdentity,
) -> dict[str, Any]:
    """Prepare the existing ProjectV2 adapter input without losing the typed ref."""
    enriched = dict(preview)
    if enriched.get("advisory_artifact_ref") != identity.technical_artifact_ref:
        raise ReadableCopilotPublicationError("preview identity mismatch")
    enriched["technical_advisory_artifact_ref"] = identity.technical_artifact_ref
    enriched["advisory_artifact_ref"] = identity.project_artifact_value
    enriched["artifact_display_title"] = identity.display_title
    enriched["artifact_actions_name"] = identity.actions_name
    enriched["artifact_run_url"] = identity.workflow_run_url
    enriched["artifact_identity_bundle_digest"] = identity.identity_bundle_digest
    return enriched


def plan_readable_issue_publication(
    *,
    base_plan: Mapping[str, Any],
    identity: ReadableCopilotPublicationIdentity,
    existing_comments: Sequence[Mapping[str, Any]],
    policy_decision_id: str,
) -> ReadableCopilotIssuePublicationPlan:
    """Reuse the existing v2 renderer, then bind its body to the readable identity."""
    if base_plan.get("valid") is not True or base_plan.get("action") != "create":
        issues = tuple(str(item) for item in base_plan.get("issues", ())) or (
            "base Copilot v2 publication plan is invalid",
        )
        return ReadableCopilotIssuePublicationPlan(
            schema=READABLE_COPILOT_ISSUE_PLAN_SCHEMA,
            valid=False,
            action="invalid",
            issues=issues,
            marker="",
            body="",
            body_sha256="",
            plan_digest="",
        )
    if not policy_decision_id.startswith("policy:"):
        raise ReadableCopilotPublicationError(
            "policy_decision_id must start with policy:"
        )
    marker = _text(base_plan.get("marker"), "marker")
    body = _text(base_plan.get("body"), "body")
    body = body.replace(
        "## Autodoc — premier avis Copilot",
        f"## {identity.display_title}",
        1,
    )
    technical_anchor = f"- Avis Copilot : `{identity.technical_artifact_ref}`"
    readable_refs = (
        f"{technical_anchor}\n"
        f"- Artefact Actions : `{identity.actions_name}`\n"
        f"- Ouvrir le run : {identity.workflow_run_url}"
    )
    if technical_anchor not in body:
        raise ReadableCopilotPublicationError(
            "base issue body does not expose the advisory reference"
        )
    body = body.replace(technical_anchor, readable_refs, 1)
    body_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    plan_digest = _digest(
        {
            "schema": READABLE_COPILOT_ISSUE_PLAN_SCHEMA,
            "repository": identity.repository,
            "issue_number": identity.issue_number,
            "policy_decision_id": policy_decision_id,
            "marker": marker,
            "body_sha256": body_sha256,
            "identity_bundle_digest": identity.identity_bundle_digest,
        }
    )
    matches = tuple(
        item for item in existing_comments if marker in str(item.get("body", ""))
    )
    if len(matches) > 1:
        return _issue_plan(
            action="collision",
            issues=("multiple existing comments carry the same marker",),
            marker=marker,
            body=body,
            body_sha256=body_sha256,
            plan_digest=plan_digest,
        )
    if not matches:
        return _issue_plan(
            action="create",
            issues=(),
            marker=marker,
            body=body,
            body_sha256=body_sha256,
            plan_digest=plan_digest,
        )
    existing = matches[0]
    if existing.get("body") == body:
        return _issue_plan(
            action="replay",
            issues=(),
            marker=marker,
            body=body,
            body_sha256=body_sha256,
            plan_digest=plan_digest,
            existing=existing,
        )
    return _issue_plan(
        action="collision",
        issues=("existing marked comment differs from the approved publication",),
        marker=marker,
        body=body,
        body_sha256=body_sha256,
        plan_digest=plan_digest,
        existing=existing,
    )


def build_combined_publication_plan(
    *,
    issue_plan: ReadableCopilotIssuePublicationPlan,
    project_plan_digest: str,
    project_action: str,
    identity: ReadableCopilotPublicationIdentity,
    policy_decision_id: str,
    project_valid: bool,
    project_issues: Sequence[str] = (),
) -> ReadableCopilotCombinedPublicationPlan:
    """Bind both previews under one operator confirmation digest."""
    issues = list(issue_plan.issues)
    issues.extend(str(item) for item in project_issues)
    if project_action not in {"update", "replay", "invalid"}:
        issues.append("unsupported ProjectV2 action")
    if not policy_decision_id.startswith("policy:"):
        issues.append("policy_decision_id must start with policy:")
    valid = issue_plan.valid and project_valid and not issues
    digest = ""
    if valid:
        digest = _digest(
            {
                "schema": READABLE_COPILOT_COMBINED_PLAN_SCHEMA,
                "repository": identity.repository,
                "issue_number": identity.issue_number,
                "policy_decision_id": policy_decision_id,
                "identity_bundle_digest": identity.identity_bundle_digest,
                "issue_action": issue_plan.action,
                "issue_plan_digest": issue_plan.plan_digest,
                "project_action": project_action,
                "project_plan_digest": project_plan_digest,
                "project_artifact_value": identity.project_artifact_value,
            }
        )
    return ReadableCopilotCombinedPublicationPlan(
        schema=READABLE_COPILOT_COMBINED_PLAN_SCHEMA,
        valid=valid,
        issues=tuple(dict.fromkeys(issues)),
        issue_action=issue_plan.action,
        project_action=project_action,
        issue_plan_digest=issue_plan.plan_digest,
        project_plan_digest=project_plan_digest,
        identity_bundle_digest=identity.identity_bundle_digest,
        plan_digest=digest,
    )


def _issue_plan(
    *,
    action: str,
    issues: tuple[str, ...],
    marker: str,
    body: str,
    body_sha256: str,
    plan_digest: str,
    existing: Mapping[str, Any] | None = None,
) -> ReadableCopilotIssuePublicationPlan:
    return ReadableCopilotIssuePublicationPlan(
        schema=READABLE_COPILOT_ISSUE_PLAN_SCHEMA,
        valid=not issues,
        action=action,
        issues=issues,
        marker=marker,
        body=body,
        body_sha256=body_sha256,
        plan_digest=plan_digest,
        existing_comment_id=(
            None if existing is None else int(existing.get("id") or 0) or None
        ),
        existing_comment_url=(
            "" if existing is None else str(existing.get("html_url") or "")
        ),
    )


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReadableCopilotPublicationError(f"{name} must be non-empty")
    return value.strip()


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ReadableCopilotPublicationError(f"{name} must be positive")
    return value


def _sha256_ref(value: object, name: str) -> str:
    text = _text(value, name)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", text):
        raise ReadableCopilotPublicationError(f"{name} must be a sha256 reference")
    return text


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
