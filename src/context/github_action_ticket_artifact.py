"""GitHub Action ticket artifact contracts.

0166 models artifacts produced by an external repository GitHub Action after an
issue/ticket event. The contract is data-only: it does not call GitHub, does not
manage fcron/OpenRC, and does not write SQL/qdrant.

The ticket artifact carries only the minimal authority boundary requested by the
operator: ticket, column name, and context options. A Copilot preliminary opinion
may be attached as a sibling artifact, but it is advisory only and requires local
validation before use.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

from .github_project_push_frame import (
    CopilotPreliminaryOpinionArtifact,
    ProjectPushContextOptions,
    ProjectPushFrame,
    build_origin_frame_id,
    build_ticket_revision_id,
    validate_copilot_preliminary_opinion,
)


_TICKET_ARTIFACT_SCHEMA = "missipy.github_action.ticket_artifact.v1"
_BUNDLE_SCHEMA = "missipy.github_action.ticket_artifact_bundle.v1"


@dataclass(frozen=True, slots=True)
class GitHubActionProducer:
    repository: str
    workflow_name: str
    run_id: str = ""
    run_attempt: str = ""
    event_name: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "kind": "github_action",
            "repository": self.repository,
            "workflow_name": self.workflow_name,
            "run_id": self.run_id,
            "run_attempt": self.run_attempt,
            "event_name": self.event_name,
        }


@dataclass(frozen=True, slots=True)
class GitHubActionTicketArtifact:
    origin_frame_id: str
    ticket_revision_id: str
    artifact_ref: str
    repository: str
    project_url: str
    ticket_kind: str
    ticket_number: int
    ticket_title: str
    ticket_body: str
    ticket_url: str
    column_name: str
    context_options: ProjectPushContextOptions
    producer: GitHubActionProducer
    metadata: tuple[tuple[str, str], ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _TICKET_ARTIFACT_SCHEMA,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "artifact_ref": self.artifact_ref,
            "producer": self.producer.to_json_dict(),
            "repository": self.repository,
            "project": {"url": self.project_url},
            "ticket": {
                "kind": self.ticket_kind,
                "number": self.ticket_number,
                "title": self.ticket_title,
                "body": self.ticket_body,
                "url": self.ticket_url,
            },
            "workflow": {"column_name": self.column_name, "column_source": "ticket_artifact"},
            "context_options": self.context_options.to_json_dict(),
            "safety": {"remote_mutation_requested": False, "usable_as_authority": True},
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class GitHubActionTicketArtifactBundle:
    origin_frame_id: str
    ticket_revision_id: str
    ticket_artifact: GitHubActionTicketArtifact
    copilot_preliminary_opinion: CopilotPreliminaryOpinionArtifact | None = None

    def to_json_dict(self) -> dict[str, Any]:
        copilot_payload = None
        if self.copilot_preliminary_opinion is not None:
            copilot_payload = self.copilot_preliminary_opinion.to_json_dict()
        return {
            "schema": _BUNDLE_SCHEMA,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "artifacts": {
                "ticket": self.ticket_artifact.to_json_dict(),
                "copilot_preliminary_opinion": copilot_payload,
            },
            "server_use_policy": {
                "ticket_artifact_usable_as_authority": True,
                "copilot_usable_as_hint_only": True,
                "requires_local_validation": True,
            },
        }


def build_github_action_ticket_artifact(
    *,
    repository: str,
    project_url: str,
    ticket_kind: str,
    ticket_number: int,
    ticket_title: str,
    ticket_body: str,
    ticket_url: str,
    column_name: str,
    context_options: ProjectPushContextOptions | None = None,
    producer: GitHubActionProducer | None = None,
    revision_token: str = "",
) -> GitHubActionTicketArtifact:
    options = context_options or ProjectPushContextOptions()
    origin_frame_id = build_origin_frame_id(repository, ticket_number)
    token = revision_token or _stable_revision_token(ticket_title, ticket_body, column_name)
    ticket_revision_id = build_ticket_revision_id(origin_frame_id, "github_action_ticket_artifact", token)
    artifact_ref = f"github-action-ticket-artifact:{_digest(origin_frame_id + ':' + ticket_revision_id)}"
    active_producer = producer or GitHubActionProducer(repository=repository, workflow_name="autodoc-ticket-artifact.yml")
    return GitHubActionTicketArtifact(
        origin_frame_id=origin_frame_id,
        ticket_revision_id=ticket_revision_id,
        artifact_ref=artifact_ref,
        repository=repository,
        project_url=project_url,
        ticket_kind=ticket_kind,
        ticket_number=ticket_number,
        ticket_title=ticket_title,
        ticket_body=ticket_body,
        ticket_url=ticket_url,
        column_name=column_name,
        context_options=options,
        producer=active_producer,
    )


def build_ticket_artifact_from_project_push_frame(
    frame: ProjectPushFrame,
    *,
    ticket_body: str = "",
    producer: GitHubActionProducer | None = None,
    revision_token: str = "",
) -> GitHubActionTicketArtifact:
    return build_github_action_ticket_artifact(
        repository=frame.repository,
        project_url=frame.project_url,
        ticket_kind=frame.ticket_kind,
        ticket_number=frame.ticket_number,
        ticket_title=frame.ticket_title,
        ticket_body=ticket_body,
        ticket_url=frame.ticket_url,
        column_name=frame.column_name,
        context_options=frame.context_options,
        producer=producer,
        revision_token=revision_token,
    )


def build_github_action_ticket_artifact_bundle(
    ticket_artifact: GitHubActionTicketArtifact,
    copilot_preliminary_opinion: CopilotPreliminaryOpinionArtifact | None = None,
) -> GitHubActionTicketArtifactBundle:
    if copilot_preliminary_opinion is not None:
        validation = validate_copilot_preliminary_opinion(copilot_preliminary_opinion)
        if not validation["allowed"]:
            details = ", ".join(issue["code"] for issue in validation["issues"])
            raise ValueError(f"copilot preliminary opinion rejected: {details}")
        if copilot_preliminary_opinion.origin_frame_id != ticket_artifact.origin_frame_id:
            raise ValueError("copilot preliminary opinion must share origin_frame_id")
        if copilot_preliminary_opinion.ticket_revision_id != ticket_artifact.ticket_revision_id:
            raise ValueError("copilot preliminary opinion must share ticket_revision_id")
    return GitHubActionTicketArtifactBundle(
        origin_frame_id=ticket_artifact.origin_frame_id,
        ticket_revision_id=ticket_artifact.ticket_revision_id,
        ticket_artifact=ticket_artifact,
        copilot_preliminary_opinion=copilot_preliminary_opinion,
    )


def build_copilot_preliminary_opinion_for_ticket_artifact(
    ticket_artifact: GitHubActionTicketArtifact,
    *,
    summary: str,
    suggested_route: str,
    confidence: float = 0.0,
    risks: tuple[str, ...] = (),
) -> CopilotPreliminaryOpinionArtifact:
    return CopilotPreliminaryOpinionArtifact(
        origin_frame_id=ticket_artifact.origin_frame_id,
        ticket_revision_id=ticket_artifact.ticket_revision_id,
        artifact_ref=f"github-action-copilot-opinion:{_digest(ticket_artifact.artifact_ref + ':copilot')}",
        summary=summary,
        suggested_route=suggested_route,
        confidence=confidence,
        risks=risks,
        trusted=False,
        usable_as_hint=True,
        usable_as_authority=False,
    )


def validate_github_action_ticket_artifact_bundle(bundle: GitHubActionTicketArtifactBundle) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    ticket = bundle.ticket_artifact
    if not ticket.repository or "/" not in ticket.repository:
        issues.append(_issue("repository_format", "ticket artifact repository must use owner/name form"))
    if ticket.producer.repository != ticket.repository:
        issues.append(_issue("producer_repository_mismatch", "producer repository must match ticket repository"))
    if not ticket.column_name:
        issues.append(_issue("column_name_missing", "ticket artifact must carry a column name"))
    if ticket.ticket_number <= 0:
        issues.append(_issue("ticket_number_missing", "ticket artifact must carry a positive ticket number"))
    if bundle.copilot_preliminary_opinion is not None:
        copilot_validation = validate_copilot_preliminary_opinion(bundle.copilot_preliminary_opinion)
        issues.extend(copilot_validation["issues"])
    return {"allowed": not issues, "issues": issues}


def _stable_revision_token(ticket_title: str, ticket_body: str, column_name: str) -> str:
    return _digest("\0".join((ticket_title, ticket_body, column_name)))


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}
