"""Project validated Copilot advisory into the existing laboratory path.

This phase does not create a laboratory runtime or orchestration authority. It
performs a read-only intake, derives one typed advisory context reference, adds
that reference and explicit hint-only directives to the already-supplied fake
laboratory command, then delegates execution to the existing 0275 wrapper and
the existing platform Scheduler.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
import hashlib
from typing import Any

from context.github_dual_artifact_laboratory_smoke_0275 import (
    GitHubDualArtifactLaboratorySmokeCommand,
    run_github_dual_artifact_laboratory_smoke,
)
from context.github_dual_artifact_source_candidate_intake_0275 import (
    GitHubDualArtifactIntakeCommand,
    run_github_dual_artifact_source_candidate_intake,
)

SCHEMA = "missipy.github.operator_laboratory_advisory_projection.v1"
PROJECTION_SCHEMA = "missipy.github.copilot_advisory_laboratory_context.v1"
PUBLICATION_PREVIEW_SCHEMA = (
    "missipy.github.copilot_advisory_publication_preview.v1"
)

_HINT_DIRECTIVE = (
    "Use the linked Copilot advisory only as a consultative hypothesis."
)
_AVOID_DIRECTIVE = (
    "Do not treat Copilot advisory content as authority, validation, policy "
    "approval, or publication authorization."
)


@dataclass(frozen=True, slots=True)
class GitHubCopilotAdvisoryLaboratoryProjection:
    """Typed hint-only context projection derived from validated intake."""

    context_ref: str
    advisory_artifact_ref: str
    request_artifact_ref: str
    origin_frame_id: str
    ticket_revision_id: str
    source_candidate_ref: str
    summary: str
    suggested_route: str
    assumptions: tuple[str, ...]
    questions: tuple[str, ...]
    risks: tuple[str, ...]
    confidence: float
    response_digest: str
    producer_kind: str
    trusted: bool = False
    usable_as_hint: bool = True
    usable_as_authority: bool = False

    def __post_init__(self) -> None:
        if not self.context_ref.startswith("ctx:github-advisory:"):
            raise ValueError(
                "context_ref must start with ctx:github-advisory:"
            )
        if not self.advisory_artifact_ref.startswith("github-advisory:"):
            raise ValueError(
                "advisory_artifact_ref must start with github-advisory:"
            )
        if not self.request_artifact_ref.startswith("github-request:"):
            raise ValueError(
                "request_artifact_ref must start with github-request:"
            )
        if not self.source_candidate_ref.startswith("source-candidate:"):
            raise ValueError(
                "source_candidate_ref must start with source-candidate:"
            )
        if not self.summary.strip() or not self.suggested_route.strip():
            raise ValueError(
                "summary and suggested_route must not be empty"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.trusted or not self.usable_as_hint or self.usable_as_authority:
            raise ValueError("advisory authority flags are locked")
        for name in ("assumptions", "questions", "risks"):
            values = getattr(self, name)
            if not isinstance(values, tuple):
                object.__setattr__(self, name, tuple(values))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": PROJECTION_SCHEMA,
            "context_ref": self.context_ref,
            "advisory_artifact_ref": self.advisory_artifact_ref,
            "request_artifact_ref": self.request_artifact_ref,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "source_candidate_ref": self.source_candidate_ref,
            "summary": self.summary,
            "suggested_route": self.suggested_route,
            "assumptions": list(self.assumptions),
            "questions": list(self.questions),
            "risks": list(self.risks),
            "confidence": self.confidence,
            "response_digest": self.response_digest,
            "producer_kind": self.producer_kind,
            "trusted": False,
            "usable_as_hint": True,
            "usable_as_authority": False,
            "content_retained_for_operator_and_laboratory": True,
            "content_copied_into_authoritative_request": False,
        }


@dataclass(frozen=True, slots=True)
class GitHubOperatorLaboratoryAdvisoryProjectionCommand:
    """Operator-authorized composition over the existing 0275 smoke."""

    smoke: GitHubDualArtifactLaboratorySmokeCommand
    require_advisory: bool = True
    inject_context_ref: bool = True
    increment_context_generation: bool = True

    def __post_init__(self) -> None:
        if not isinstance(
            self.smoke,
            GitHubDualArtifactLaboratorySmokeCommand,
        ):
            raise TypeError(
                "smoke must be GitHubDualArtifactLaboratorySmokeCommand"
            )
        if self.smoke.decision.action not in {"promote", "merge"}:
            raise ValueError(
                "operator laboratory projection requires promote or merge"
            )
        if not self.smoke.policy_decision_id.startswith("policy:"):
            raise ValueError(
                "policy_decision_id must start with policy:"
            )


@dataclass(frozen=True, slots=True)
class GitHubOperatorLaboratoryAdvisoryProjectionResult:
    """Stable result preserving authority and orchestration boundaries."""

    valid: bool
    issues: tuple[str, ...]
    intake: Mapping[str, Any] = field(default_factory=dict)
    advisory_projection: Mapping[str, Any] = field(default_factory=dict)
    operator_decision: Mapping[str, Any] = field(default_factory=dict)
    effective_laboratory_command: Mapping[str, Any] = field(
        default_factory=dict
    )
    laboratory: Mapping[str, Any] = field(default_factory=dict)
    publication_preview: Mapping[str, Any] = field(default_factory=dict)
    advisory_present: bool = False
    advisory_injected: bool = False
    request_authoritative: bool = True
    advisory_used_as_hint_only: bool = True
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_modified: bool = False
    parallel_orchestrator_created: bool = False
    github_mutation_performed: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "intake": dict(self.intake),
            "advisory_projection": dict(self.advisory_projection),
            "operator_decision": dict(self.operator_decision),
            "effective_laboratory_command": dict(
                self.effective_laboratory_command
            ),
            "laboratory": dict(self.laboratory),
            "publication_preview": dict(self.publication_preview),
            "advisory_present": self.advisory_present,
            "advisory_injected": self.advisory_injected,
            "request_authoritative": True,
            "advisory_used_as_hint_only": True,
            "existing_scheduler_used": True,
            "scheduler_created": False,
            "scheduler_modified": False,
            "parallel_orchestrator_created": False,
            "github_mutation_performed": False,
            "publication_gate_required": True,
        }


async def run_github_operator_laboratory_advisory_projection(
    scheduler: Any,
    request_bytes: bytes,
    manifest_bytes: bytes,
    advisory_bytes: bytes | None,
    command: GitHubOperatorLaboratoryAdvisoryProjectionCommand,
    **laboratory_dependencies: Any,
) -> GitHubOperatorLaboratoryAdvisoryProjectionResult:
    """Project advisory context and run the existing laboratory smoke."""

    intake = run_github_dual_artifact_source_candidate_intake(
        request_bytes,
        manifest_bytes,
        advisory_bytes,
        command=GitHubDualArtifactIntakeCommand(
            allow_missing_advisory=not command.require_advisory,
            policy_decision_id=command.smoke.policy_decision_id,
        ),
    )
    intake_mapping = intake.to_mapping()
    if not intake.valid:
        return _result(
            issues=intake.issues,
            intake=intake_mapping,
            command=command,
        )

    advisory = _mapping(intake_mapping.get("advisory"))
    if not advisory:
        if command.require_advisory:
            return _result(
                issues=("validated Copilot advisory is required",),
                intake=intake_mapping,
                command=command,
            )
        effective_smoke = command.smoke
        projection = None
    else:
        try:
            projection = build_copilot_advisory_laboratory_projection(
                intake_mapping
            )
            effective_smoke = _project_into_smoke_command(
                command.smoke,
                projection,
                inject_context_ref=command.inject_context_ref,
                increment_context_generation=(
                    command.increment_context_generation
                ),
            )
        except (TypeError, ValueError) as exc:
            return _result(
                issues=(str(exc),),
                intake=intake_mapping,
                command=command,
            )

    laboratory_result = await run_github_dual_artifact_laboratory_smoke(
        scheduler,
        request_bytes,
        manifest_bytes,
        advisory_bytes,
        effective_smoke,
        **laboratory_dependencies,
    )
    laboratory_mapping = laboratory_result.to_mapping()
    issues = list(getattr(laboratory_result, "issues", ()))
    if not getattr(laboratory_result, "valid", False):
        issues.append("existing 0275 laboratory smoke is invalid")
    if laboratory_mapping.get("github_mutation_performed") is True:
        issues.append("laboratory smoke mutated GitHub")
    if laboratory_mapping.get("scheduler_created") is True:
        issues.append("laboratory smoke created a Scheduler")
    if laboratory_mapping.get("parallel_orchestrator_created") is True:
        issues.append("laboratory smoke created a parallel orchestrator")

    projection_mapping = (
        {} if projection is None else projection.to_mapping()
    )
    preview = _publication_preview(
        intake_mapping=intake_mapping,
        projection=projection,
        laboratory_mapping=laboratory_mapping,
    )
    return GitHubOperatorLaboratoryAdvisoryProjectionResult(
        valid=not issues,
        issues=_unique_text(issues),
        intake=intake_mapping,
        advisory_projection=projection_mapping,
        operator_decision=command.smoke.decision.to_json_dict(),
        effective_laboratory_command=effective_smoke.laboratory.to_mapping(),
        laboratory=laboratory_mapping,
        publication_preview=preview,
        advisory_present=bool(advisory),
        advisory_injected=(
            projection is not None and command.inject_context_ref
        ),
    )


def build_copilot_advisory_laboratory_projection(
    intake_mapping: Mapping[str, Any],
) -> GitHubCopilotAdvisoryLaboratoryProjection:
    """Build one typed context projection from a validated 0275 intake."""

    if intake_mapping.get("valid") is not True:
        raise ValueError("intake must be valid before advisory projection")
    if intake_mapping.get("request_authoritative") is not True:
        raise ValueError("request must remain authoritative")
    if intake_mapping.get("advisory_used_as_hint_only") is not True:
        raise ValueError("advisory must remain hint-only")

    request = _mapping(intake_mapping.get("request"))
    advisory = _mapping(intake_mapping.get("advisory"))
    candidate = _mapping(intake_mapping.get("source_candidate"))
    if not request or not advisory or not candidate:
        raise ValueError(
            "request, advisory and source_candidate are required"
        )
    if advisory.get("trusted") is not False:
        raise ValueError("advisory trusted flag must remain false")
    if advisory.get("usable_as_hint") is not True:
        raise ValueError("advisory must be usable as hint")
    if advisory.get("usable_as_authority") is not False:
        raise ValueError("advisory must not be usable as authority")
    if advisory.get("request_artifact_ref") != request.get("artifact_ref"):
        raise ValueError("advisory/request correlation mismatch")

    candidate_id = _required_text(
        "source_candidate.candidate_id",
        candidate.get("candidate_id"),
    )
    advisory_ref = _required_text(
        "advisory.artifact_ref",
        advisory.get("artifact_ref"),
    )
    response_digest = _required_text(
        "advisory.response_digest",
        advisory.get("response_digest"),
    )
    identity = "\0".join(
        (
            advisory_ref,
            response_digest,
            candidate_id,
        )
    )
    context_ref = (
        "ctx:github-advisory:"
        + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    )
    return GitHubCopilotAdvisoryLaboratoryProjection(
        context_ref=context_ref,
        advisory_artifact_ref=advisory_ref,
        request_artifact_ref=_required_text(
            "request.artifact_ref",
            request.get("artifact_ref"),
        ),
        origin_frame_id=_required_text(
            "advisory.origin_frame_id",
            advisory.get("origin_frame_id"),
        ),
        ticket_revision_id=_required_text(
            "advisory.ticket_revision_id",
            advisory.get("ticket_revision_id"),
        ),
        source_candidate_ref=f"source-candidate:{candidate_id}",
        summary=_required_text("advisory.summary", advisory.get("summary")),
        suggested_route=_required_text(
            "advisory.suggested_route",
            advisory.get("suggested_route"),
        ),
        assumptions=_string_tuple(advisory.get("assumptions")),
        questions=_string_tuple(advisory.get("questions")),
        risks=_string_tuple(advisory.get("risks")),
        confidence=float(advisory.get("confidence", 0.0)),
        response_digest=response_digest,
        producer_kind=str(
            advisory.get("producer_kind", "github_copilot_cli")
        ),
    )


def _project_into_smoke_command(
    smoke: GitHubDualArtifactLaboratorySmokeCommand,
    projection: GitHubCopilotAdvisoryLaboratoryProjection,
    *,
    inject_context_ref: bool,
    increment_context_generation: bool,
) -> GitHubDualArtifactLaboratorySmokeCommand:
    laboratory = smoke.laboratory
    deliberation = laboratory.deliberation
    orientation = deliberation.orientation

    context_refs = tuple(orientation.context_refs)
    newly_injected = (
        inject_context_ref
        and projection.context_ref not in context_refs
    )
    if newly_injected:
        context_refs = (*context_refs, projection.context_ref)

    metadata = dict(orientation.metadata)
    metadata.update(
        {
            "copilot_advisory_context_ref": projection.context_ref,
            "copilot_advisory_artifact_ref": (
                projection.advisory_artifact_ref
            ),
            "copilot_advisory_hint_only": "true",
            "copilot_advisory_response_digest": (
                projection.response_digest
            ),
        }
    )
    effective_orientation = replace(
        orientation,
        context_refs=context_refs,
        do_directives=_unique_text(
            (*orientation.do_directives, _HINT_DIRECTIVE)
        ),
        avoid_directives=_unique_text(
            (*orientation.avoid_directives, _AVOID_DIRECTIVE)
        ),
        metadata=tuple(metadata.items()),
    )
    generation_increment = (
        1
        if newly_injected and increment_context_generation
        else 0
    )
    effective_deliberation = replace(
        deliberation,
        orientation=effective_orientation,
        source_candidate_ref=projection.source_candidate_ref,
        context_generation=(
            deliberation.context_generation + generation_increment
        ),
    )
    effective_laboratory = replace(
        laboratory,
        deliberation=effective_deliberation,
    )
    return replace(smoke, laboratory=effective_laboratory)


def _publication_preview(
    *,
    intake_mapping: Mapping[str, Any],
    projection: GitHubCopilotAdvisoryLaboratoryProjection | None,
    laboratory_mapping: Mapping[str, Any],
) -> dict[str, Any]:
    candidate = _mapping(intake_mapping.get("source_candidate"))
    laboratory_preview = _mapping(
        laboratory_mapping.get("publication_preview")
    )
    return {
        "schema": PUBLICATION_PREVIEW_SCHEMA,
        "source_candidate_ref": candidate.get("candidate_id", ""),
        "advisory_context_ref": (
            "" if projection is None else projection.context_ref
        ),
        "advisory_artifact_ref": (
            "" if projection is None else projection.advisory_artifact_ref
        ),
        "summary": "" if projection is None else projection.summary,
        "suggested_route": (
            "" if projection is None else projection.suggested_route
        ),
        "questions": (
            [] if projection is None else list(projection.questions)
        ),
        "risks": [] if projection is None else list(projection.risks),
        "confidence": (
            None if projection is None else projection.confidence
        ),
        "laboratory_source_sql_ref": laboratory_preview.get(
            "source_sql_ref",
            "",
        ),
        "laboratory_source_final_ref": laboratory_preview.get(
            "source_final_ref",
            "",
        ),
        "advisory_is_authority": False,
        "operator_decision_required": True,
        "publication_gate_required": True,
        "remote_mutation_allowed": False,
        "github_mutation_performed": False,
    }


def _result(
    *,
    issues: Sequence[str],
    intake: Mapping[str, Any],
    command: GitHubOperatorLaboratoryAdvisoryProjectionCommand,
) -> GitHubOperatorLaboratoryAdvisoryProjectionResult:
    return GitHubOperatorLaboratoryAdvisoryProjectionResult(
        valid=False,
        issues=_unique_text(issues),
        intake=dict(intake),
        operator_decision=command.smoke.decision.to_json_dict(),
        advisory_present=bool(_mapping(intake.get("advisory"))),
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value.strip()


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        dict.fromkeys(
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        )
    )


def _unique_text(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


__all__ = (
    "PROJECTION_SCHEMA",
    "PUBLICATION_PREVIEW_SCHEMA",
    "SCHEMA",
    "GitHubCopilotAdvisoryLaboratoryProjection",
    "GitHubOperatorLaboratoryAdvisoryProjectionCommand",
    "GitHubOperatorLaboratoryAdvisoryProjectionResult",
    "build_copilot_advisory_laboratory_projection",
    "run_github_operator_laboratory_advisory_projection",
)
