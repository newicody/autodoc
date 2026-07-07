"""Project push frame contracts for external GitHub task artifacts.

These are data-only contracts. They do not call GitHub, fcron, SQL, qdrant,
openvino, an LLM, OpenRC, or the MissiPy Scheduler.

A project push frame groups artifacts produced from the same external ticket:
ticket snapshots, column/status changes, optional Copilot preliminary opinions,
local inference responses, and user decisions. History is append-only: changes
are represented as new revisions/decision artifacts rather than silent mutation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Mapping


_FRAME_SCHEMA = "missipy.github_project.project_push_frame.v1"
_REVISION_SCHEMA = "missipy.github_project.project_push_frame_revision.v1"
_COPILOT_SCHEMA = "missipy.github_project.copilot_preliminary_opinion.v1"
_LOCAL_RESPONSE_SCHEMA = "missipy.github_project.local_inference_response.v1"
_USER_DECISION_SCHEMA = "missipy.github_project.user_artifact_decision.v1"


@dataclass(frozen=True, slots=True)
class ProjectPushContextOptions:
    include_total_project: bool = False
    include_current_ticket: bool = True
    include_repository_context: bool = False
    include_linked_tickets: bool = False
    include_recent_artifacts: bool = False
    requested_depth: str = "normal"

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "include_total_project": self.include_total_project,
            "include_current_ticket": self.include_current_ticket,
            "include_repository_context": self.include_repository_context,
            "include_linked_tickets": self.include_linked_tickets,
            "include_recent_artifacts": self.include_recent_artifacts,
            "requested_depth": self.requested_depth,
        }


@dataclass(frozen=True, slots=True)
class ProjectPushFrame:
    origin_frame_id: str
    repository: str
    project_url: str
    ticket_kind: str
    ticket_number: int
    ticket_title: str
    ticket_url: str
    column_name: str
    context_options: ProjectPushContextOptions = field(default_factory=ProjectPushContextOptions)
    metadata: tuple[tuple[str, str], ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _FRAME_SCHEMA,
            "origin_frame_id": self.origin_frame_id,
            "repository": self.repository,
            "project_url": self.project_url,
            "ticket": {
                "kind": self.ticket_kind,
                "number": self.ticket_number,
                "title": self.ticket_title,
                "url": self.ticket_url,
            },
            "workflow": {"column_name": self.column_name},
            "context_options": self.context_options.to_json_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProjectPushFrameRevision:
    origin_frame_id: str
    ticket_revision_id: str
    event_kind: str
    column_name: str
    previous_column_name: str | None = None
    artifact_refs: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _REVISION_SCHEMA,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "event_kind": self.event_kind,
            "previous_column_name": self.previous_column_name,
            "column_name": self.column_name,
            "artifact_refs": list(self.artifact_refs),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CopilotPreliminaryOpinionArtifact:
    origin_frame_id: str
    ticket_revision_id: str
    artifact_ref: str
    summary: str
    suggested_route: str
    confidence: float = 0.0
    risks: tuple[str, ...] = ()
    trusted: bool = False
    usable_as_hint: bool = True
    usable_as_authority: bool = False

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _COPILOT_SCHEMA,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "artifact_ref": self.artifact_ref,
            "producer": {"kind": "github_action_copilot", "trusted": self.trusted},
            "opinion": {
                "summary": self.summary,
                "suggested_route": self.suggested_route,
                "risks": list(self.risks),
                "confidence": self.confidence,
            },
            "server_use_policy": {
                "usable_as_hint": self.usable_as_hint,
                "usable_as_authority": self.usable_as_authority,
                "requires_local_validation": True,
            },
        }


@dataclass(frozen=True, slots=True)
class LocalInferenceResponseArtifact:
    origin_frame_id: str
    ticket_revision_id: str
    artifact_ref: str
    title: str
    summary: str
    source_artifact_refs: tuple[str, ...]
    status: str = "current"
    metadata: tuple[tuple[str, str], ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _LOCAL_RESPONSE_SCHEMA,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "artifact_ref": self.artifact_ref,
            "title": self.title,
            "summary": self.summary,
            "source_artifact_refs": list(self.source_artifact_refs),
            "status": self.status,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class UserArtifactDecision:
    origin_frame_id: str
    target_artifact_ref: str
    decision: str
    rating: int | None = None
    locked: bool = False
    detached: bool = False
    deleted: bool = False
    comment: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _USER_DECISION_SCHEMA,
            "origin_frame_id": self.origin_frame_id,
            "target_artifact_ref": self.target_artifact_ref,
            "decision": self.decision,
            "rating": self.rating,
            "locked": self.locked,
            "detached": self.detached,
            "deleted": self.deleted,
            "comment": self.comment,
        }


def build_project_push_frame_from_ticket_payload(payload: Mapping[str, Any]) -> ProjectPushFrame:
    repository = str(payload.get("repository", ""))
    ticket = payload.get("ticket") if isinstance(payload.get("ticket"), Mapping) else {}
    project = payload.get("project") if isinstance(payload.get("project"), Mapping) else {}
    workflow = payload.get("workflow") if isinstance(payload.get("workflow"), Mapping) else {}
    options = payload.get("context_options") if isinstance(payload.get("context_options"), Mapping) else {}

    ticket_number = int(ticket.get("number", 0))
    origin_frame_id = str(payload.get("origin_frame_id") or build_origin_frame_id(repository, ticket_number))

    return ProjectPushFrame(
        origin_frame_id=origin_frame_id,
        repository=repository,
        project_url=str(project.get("url", payload.get("project_url", ""))),
        ticket_kind=str(ticket.get("kind", "issue")),
        ticket_number=ticket_number,
        ticket_title=str(ticket.get("title", "")),
        ticket_url=str(ticket.get("url", "")),
        column_name=str(workflow.get("column_name", workflow.get("column", ""))),
        context_options=ProjectPushContextOptions(
            include_total_project=bool(options.get("include_total_project", False)),
            include_current_ticket=bool(options.get("include_current_ticket", True)),
            include_repository_context=bool(options.get("include_repository_context", False)),
            include_linked_tickets=bool(options.get("include_linked_tickets", False)),
            include_recent_artifacts=bool(options.get("include_recent_artifacts", False)),
            requested_depth=str(options.get("requested_depth", "normal")),
        ),
    )


def build_origin_frame_id(repository: str, ticket_number: int) -> str:
    return f"github-frame:{repository}/issues/{ticket_number}"


def build_ticket_revision_id(origin_frame_id: str, event_kind: str, revision_token: str) -> str:
    digest = hashlib.sha256(f"{origin_frame_id}\0{event_kind}\0{revision_token}".encode("utf-8")).hexdigest()[:16]
    return f"github-ticket-revision:{digest}"


def validate_copilot_preliminary_opinion(opinion: CopilotPreliminaryOpinionArtifact) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if opinion.usable_as_authority:
        issues.append({"code": "copilot_authority_forbidden", "message": "Copilot preliminary opinion must not be authority"})
    if opinion.trusted:
        issues.append({"code": "copilot_trusted_forbidden", "message": "Copilot preliminary opinion is advisory and untrusted by default"})
    if not opinion.usable_as_hint:
        issues.append({"code": "copilot_hint_disabled", "message": "Copilot opinion should be usable only as a hint"})
    return {"allowed": not issues, "issues": issues}
