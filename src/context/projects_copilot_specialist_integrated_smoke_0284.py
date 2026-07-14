"""Integrated Projects/Copilot/portable-specialist smoke for phase 0284-r7.

The module composes existing read-only GitHub dual-artifact assembly, the
operator-approved hint-only Copilot projection, the 0284-r6 real-memory
closure and the existing 0281 controlled publication planner.

It never fetches GitHub, creates a Scheduler, executes a GitHub mutation or
owns ProjectV2 views.  The views and their mutation script remain in the
bundle copied to ``newicody/projects``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from contracts.scheduler import SchedulerContract
from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubControlledAdvisoryIssuePublicationCommand,
    GitHubControlledAdvisoryIssuePublicationPlan,
    GitHubIssueCommentSnapshot,
    plan_github_controlled_advisory_issue_publication,
)
from context.github_dual_artifact_run_assembly_0281 import (
    GitHubDualArtifactRunAssemblyCommand,
    GitHubDualArtifactRunAssemblyPolicy,
    GitHubDualArtifactRunAssemblyResult,
    GitHubDualArtifactRunMember,
    run_github_dual_artifact_run_assembly,
)
from context.github_operator_laboratory_advisory_projection_0281 import (
    PUBLICATION_PREVIEW_SCHEMA,
    GitHubCopilotAdvisoryLaboratoryProjection,
    build_copilot_advisory_laboratory_projection,
)
from context.portable_specialist_real_memory_closure_0284 import (
    PortableSpecialistRealMemoryClosureCommand,
    PortableSpecialistRealMemoryClosureResult,
    run_portable_specialist_real_memory_closure,
)

PROJECTS_COPILOT_SPECIALIST_INTEGRATED_SMOKE_VERSION = "0284.r7"
PROJECTS_COPILOT_SPECIALIST_COMMAND_SCHEMA = (
    "missipy.github.projects_copilot_specialist_smoke_command.v1"
)
PROJECTS_COPILOT_SPECIALIST_RESULT_SCHEMA = (
    "missipy.github.projects_copilot_specialist_smoke_result.v1"
)
PROJECTS_FIELD_PREVIEW_SCHEMA = (
    "autodoc.github.copilot_projectv2_projection_preview.v1"
)

AssemblyRunner = Callable[..., GitHubDualArtifactRunAssemblyResult]
ProjectionBuilder = Callable[
    [Mapping[str, Any]], GitHubCopilotAdvisoryLaboratoryProjection
]
MemoryRunner = Callable[..., Any]
PublicationPlanner = Callable[
    [GitHubControlledAdvisoryIssuePublicationCommand],
    GitHubControlledAdvisoryIssuePublicationPlan,
]


class ProjectsCopilotSpecialistIntegratedSmokeError(RuntimeError):
    """Raised when the r7 composition would weaken an existing boundary."""


@dataclass(frozen=True, slots=True)
class ProjectsCopilotSpecialistIntegratedSmokeCommand:
    """One operator-approved local composition over already-downloaded artifacts."""

    repository: str
    run_id: str
    issue_number: int
    members: tuple[GitHubDualArtifactRunMember, ...]
    policy_decision_id: str
    operator_reason: str
    cycle_ref: str
    updated_date: str
    memory: PortableSpecialistRealMemoryClosureCommand
    require_advisory: bool = True
    existing_comments: tuple[GitHubIssueCommentSnapshot, ...] = ()
    schema: str = PROJECTS_COPILOT_SPECIALIST_COMMAND_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != PROJECTS_COPILOT_SPECIALIST_COMMAND_SCHEMA:
            raise ProjectsCopilotSpecialistIntegratedSmokeError(
                "unsupported integrated smoke command schema"
            )
        if "/" not in self.repository:
            raise ValueError("repository must be owner/name")
        if not self.run_id.strip():
            raise ValueError("run_id must not be empty")
        if self.issue_number <= 0:
            raise ValueError("issue_number must be > 0")
        if not isinstance(self.members, tuple):
            object.__setattr__(self, "members", tuple(self.members))
        if not self.policy_decision_id.startswith("policy:"):
            raise ValueError("policy_decision_id must start with policy:")
        if not self.operator_reason.strip():
            raise ValueError("operator_reason must not be empty")
        if not self.cycle_ref.strip():
            raise ValueError("cycle_ref must not be empty")
        try:
            date.fromisoformat(self.updated_date)
        except ValueError as exc:
            raise ValueError("updated_date must use YYYY-MM-DD") from exc
        if not isinstance(self.memory, PortableSpecialistRealMemoryClosureCommand):
            raise TypeError(
                "memory must be PortableSpecialistRealMemoryClosureCommand"
            )
        if not isinstance(self.existing_comments, tuple):
            object.__setattr__(
                self,
                "existing_comments",
                tuple(self.existing_comments),
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "repository": self.repository,
            "run_id": self.run_id,
            "issue_number": self.issue_number,
            "member_count": len(self.members),
            "policy_decision_id": self.policy_decision_id,
            "operator_reason": self.operator_reason,
            "cycle_ref": self.cycle_ref,
            "updated_date": self.updated_date,
            "require_advisory": self.require_advisory,
            "existing_comment_count": len(self.existing_comments),
            "operator_decision": "approve",
            "request_authoritative": True,
            "advisory_is_authority": False,
            "github_mutation_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class ProjectsCopilotSpecialistIntegratedSmokeResult:
    """Proof of one local integrated path and its controlled remote plans."""

    valid: bool
    issues: tuple[str, ...]
    command: ProjectsCopilotSpecialistIntegratedSmokeCommand
    assembly: Mapping[str, Any] = field(default_factory=dict)
    advisory_projection: Mapping[str, Any] = field(default_factory=dict)
    memory: Mapping[str, Any] = field(default_factory=dict)
    publication_preview: Mapping[str, Any] = field(default_factory=dict)
    publication_plan: Mapping[str, Any] = field(default_factory=dict)
    project_fields_preview: Mapping[str, Any] = field(default_factory=dict)
    artifact_correlation_verified: bool = False
    advisory_context_injected: bool = False
    source_candidate_injected: bool = False
    request_authoritative: bool = True
    advisory_used_as_hint_only: bool = True
    real_memory_closed: bool = False
    publication_plan_ready: bool = False
    projects_projection_ready: bool = False
    integrated_closed_loop_complete: bool = False
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_modified: bool = False
    parallel_orchestrator_created: bool = False
    github_mutation_performed: bool = False
    projectv2_mutation_performed: bool = False
    schema: str = PROJECTS_COPILOT_SPECIALIST_RESULT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != PROJECTS_COPILOT_SPECIALIST_RESULT_SCHEMA:
            raise ProjectsCopilotSpecialistIntegratedSmokeError(
                "unsupported integrated smoke result schema"
            )
        forbidden = (
            not self.existing_scheduler_used,
            self.scheduler_created,
            self.scheduler_modified,
            self.parallel_orchestrator_created,
            self.github_mutation_performed,
            self.projectv2_mutation_performed,
            not self.request_authoritative,
            not self.advisory_used_as_hint_only,
        )
        if any(forbidden):
            raise ProjectsCopilotSpecialistIntegratedSmokeError(
                "r7 must preserve authority, Scheduler and remote-mutation boundaries"
            )
        if self.valid and self.integrated_closed_loop_complete:
            required = (
                self.artifact_correlation_verified,
                self.advisory_context_injected,
                self.source_candidate_injected,
                self.real_memory_closed,
                self.publication_plan_ready,
                self.projects_projection_ready,
            )
            if not all(required):
                raise ProjectsCopilotSpecialistIntegratedSmokeError(
                    "complete r7 result requires every integrated boundary proof"
                )

    def to_mapping(self) -> dict[str, object]:
        live_path_status = (
            "green"
            if self.valid and self.integrated_closed_loop_complete
            else "red"
            if self.issues
            else "n/a"
        )
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "command": self.command.to_mapping(),
            "assembly": dict(self.assembly),
            "advisory_projection": dict(self.advisory_projection),
            "memory": dict(self.memory),
            "publication_preview": dict(self.publication_preview),
            "publication_plan": dict(self.publication_plan),
            "project_fields_preview": dict(self.project_fields_preview),
            "artifact_correlation_verified": self.artifact_correlation_verified,
            "advisory_context_injected": self.advisory_context_injected,
            "source_candidate_injected": self.source_candidate_injected,
            "request_authoritative": True,
            "advisory_used_as_hint_only": True,
            "real_memory_closed": self.real_memory_closed,
            "publication_plan_ready": self.publication_plan_ready,
            "projects_projection_ready": self.projects_projection_ready,
            "integrated_closed_loop_complete": (
                self.integrated_closed_loop_complete
            ),
            "existing_scheduler_used": True,
            "scheduler_created": False,
            "scheduler_modified": False,
            "parallel_orchestrator_created": False,
            "github_mutation_performed": False,
            "projectv2_mutation_performed": False,
            "publication_execution_required": True,
            "projectv2_projection_execution_required": True,
            "projects_configuration_owned_by": "newicody/projects",
            "sql_remains_authority": True,
            "qdrant_projection_recall_only": True,
            "eventbus_observation_only": True,
            "live_path_status": live_path_status,
            "live_path_uses_real_backend": (
                self.valid and self.integrated_closed_loop_complete
            ),
        }


async def run_projects_copilot_specialist_integrated_smoke(
    scheduler: SchedulerContract,
    command: ProjectsCopilotSpecialistIntegratedSmokeCommand,
    *,
    assembly_runner: AssemblyRunner = run_github_dual_artifact_run_assembly,
    projection_builder: ProjectionBuilder = (
        build_copilot_advisory_laboratory_projection
    ),
    memory_runner: MemoryRunner = run_portable_specialist_real_memory_closure,
    publication_planner: PublicationPlanner = (
        plan_github_controlled_advisory_issue_publication
    ),
    **memory_dependencies: Any,
) -> ProjectsCopilotSpecialistIntegratedSmokeResult:
    """Run the integrated local path and produce no-write remote plans."""

    if not isinstance(scheduler, SchedulerContract):
        raise TypeError("scheduler must implement SchedulerContract")
    if not isinstance(
        command,
        ProjectsCopilotSpecialistIntegratedSmokeCommand,
    ):
        raise TypeError(
            "command must be ProjectsCopilotSpecialistIntegratedSmokeCommand"
        )

    assembly_result = assembly_runner(
        GitHubDualArtifactRunAssemblyCommand(
            repository=command.repository,
            run_id=command.run_id,
            members=command.members,
        ),
        GitHubDualArtifactRunAssemblyPolicy(
            allow_missing_advisory=not command.require_advisory,
        ),
    )
    assembly = assembly_result.to_mapping()
    if not assembly_result.valid:
        return _result(command, issues=assembly_result.issues, assembly=assembly)

    intake = _mapping(assembly.get("intake"), name="assembly.intake")
    request = _mapping(intake.get("request"), name="intake.request")
    advisory = _mapping(intake.get("advisory"), name="intake.advisory")
    candidate = _mapping(
        intake.get("source_candidate"),
        name="intake.source_candidate",
    )
    issues: list[str] = []
    if intake.get("request_authoritative") is not True:
        issues.append("dual-artifact intake must keep the request authoritative")
    if intake.get("advisory_used_as_hint_only") is not True:
        issues.append("dual-artifact intake must keep advisory hint-only")
    if command.require_advisory and not advisory:
        issues.append("validated Copilot advisory is required")
    if request.get("repository") != command.repository:
        issues.append("authoritative request repository does not match command")
    if issues:
        return _result(command, issues=issues, assembly=assembly)

    try:
        projection = projection_builder(intake)
    except (TypeError, ValueError) as exc:
        return _result(command, issues=(str(exc),), assembly=assembly)
    projection_mapping = projection.to_mapping()

    memory_command_mapping = command.memory.specialist_smoke.to_mapping()
    memory_strings = frozenset(_all_strings(memory_command_mapping))
    candidate_id = _required_text(
        "source_candidate.candidate_id",
        candidate.get("candidate_id"),
    )
    typed_candidate_ref = f"source-candidate:{candidate_id}"
    advisory_context_injected = projection.context_ref in memory_strings
    source_candidate_injected = (
        candidate_id in memory_strings or typed_candidate_ref in memory_strings
    )
    if not advisory_context_injected:
        issues.append(
            "r6 specialist command does not contain the validated advisory context"
        )
    if not source_candidate_injected:
        issues.append(
            "r6 specialist command does not contain the authoritative candidate"
        )
    memory_policy_id = (
        command.memory.projection_configuration.effect_gate.policy_decision_id
    )
    if memory_policy_id != command.policy_decision_id:
        issues.append("GitHub and real-memory paths must share policy_decision_id")
    if issues:
        return _result(
            command,
            issues=issues,
            assembly=assembly,
            advisory_projection=projection_mapping,
            artifact_correlation_verified=True,
            advisory_context_injected=advisory_context_injected,
            source_candidate_injected=source_candidate_injected,
        )

    memory_result: PortableSpecialistRealMemoryClosureResult = await memory_runner(
        scheduler,
        command.memory,
        **memory_dependencies,
    )
    memory_mapping = memory_result.to_mapping()
    issues.extend(memory_result.issues)
    real_memory_closed = bool(
        memory_result.valid
        and not memory_result.preview_only
        and memory_result.memory_closed
        and memory_result.real_sql_authority_used
        and memory_result.real_openvino_e5_used
        and memory_result.real_qdrant_projection_used
        and memory_result.real_qdrant_recall_used
        and memory_result.sql_rehydration_verified
    )
    if not real_memory_closed:
        issues.append("portable specialist real-memory closure is incomplete")

    publication_preview = _publication_preview(
        candidate_id=candidate_id,
        projection=projection,
        memory_mapping=memory_mapping,
    )
    plan = publication_planner(
        GitHubControlledAdvisoryIssuePublicationCommand(
            repository=command.repository,
            issue_number=command.issue_number,
            policy_decision_id=command.policy_decision_id,
            operator_decision="approve",
            publication_preview=publication_preview,
            existing_comments=command.existing_comments,
        )
    )
    publication_plan = plan.to_mapping()
    publication_plan_ready = bool(
        plan.valid and plan.action in {"create", "replay"}
    )
    if not publication_plan_ready:
        issues.extend(plan.issues or ("controlled publication plan is not ready",))

    project_fields_preview = _project_fields_preview(
        command=command,
        projection=projection,
    )
    projects_projection_ready = _project_fields_preview_valid(
        project_fields_preview
    )
    if not projects_projection_ready:
        issues.append("Projects Copilot field projection preview is invalid")

    normalized = _unique_text(issues)
    complete = bool(
        not normalized
        and real_memory_closed
        and publication_plan_ready
        and projects_projection_ready
    )
    return _result(
        command,
        issues=normalized,
        assembly=assembly,
        advisory_projection=projection_mapping,
        memory=memory_mapping,
        publication_preview=publication_preview,
        publication_plan=publication_plan,
        project_fields_preview=project_fields_preview,
        artifact_correlation_verified=True,
        advisory_context_injected=advisory_context_injected,
        source_candidate_injected=source_candidate_injected,
        real_memory_closed=real_memory_closed,
        publication_plan_ready=publication_plan_ready,
        projects_projection_ready=projects_projection_ready,
        integrated_closed_loop_complete=complete,
    )


def _publication_preview(
    *,
    candidate_id: str,
    projection: GitHubCopilotAdvisoryLaboratoryProjection,
    memory_mapping: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": PUBLICATION_PREVIEW_SCHEMA,
        "source_candidate_ref": candidate_id,
        "advisory_context_ref": projection.context_ref,
        "advisory_artifact_ref": projection.advisory_artifact_ref,
        "summary": projection.summary,
        "suggested_route": projection.suggested_route,
        "questions": list(projection.questions),
        "risks": list(projection.risks),
        "confidence": projection.confidence,
        "laboratory_source_sql_ref": str(memory_mapping.get("sql_ref", "")),
        "laboratory_source_final_ref": _first_value_for_key(
            memory_mapping,
            "final_ref",
        ),
        "operator_decision_required": True,
        "publication_gate_required": True,
        "advisory_is_authority": False,
        "request_authoritative": True,
        "github_mutation_performed": False,
        "remote_mutation_allowed": False,
    }


def _project_fields_preview(
    *,
    command: ProjectsCopilotSpecialistIntegratedSmokeCommand,
    projection: GitHubCopilotAdvisoryLaboratoryProjection,
) -> dict[str, Any]:
    return {
        "schema": PROJECTS_FIELD_PREVIEW_SCHEMA,
        "repository": command.repository,
        "issue_number": command.issue_number,
        "policy_decision_id": command.policy_decision_id,
        "fields": {
            "Copilot": "Terminé",
            "Avis Copilot": projection.summary,
            "Route Copilot": projection.suggested_route,
            "Confiance Copilot": projection.confidence,
            "Dernière mise à jour": command.updated_date,
            "Artefact": projection.advisory_artifact_ref,
            "Cycle": command.cycle_ref,
        },
        "forbidden_fields_untouched": ["Résumé", "Serveur"],
        "request_authoritative": True,
        "advisory_is_authority": False,
        "operator_decision_required": True,
        "remote_mutation_allowed": False,
        "projectv2_mutation_performed": False,
        "configuration_owner": "newicody/projects",
        "execution_adapter": (
            "templates/github/projects-repository/scripts/"
            "project_copilot_advisory_fields.py"
        ),
    }


def _project_fields_preview_valid(preview: Mapping[str, Any]) -> bool:
    fields = preview.get("fields")
    if preview.get("schema") != PROJECTS_FIELD_PREVIEW_SCHEMA:
        return False
    if not isinstance(fields, Mapping):
        return False
    expected = {
        "Copilot",
        "Avis Copilot",
        "Route Copilot",
        "Confiance Copilot",
        "Dernière mise à jour",
        "Artefact",
        "Cycle",
    }
    if set(fields) != expected:
        return False
    return (
        preview.get("request_authoritative") is True
        and preview.get("advisory_is_authority") is False
        and preview.get("operator_decision_required") is True
        and preview.get("remote_mutation_allowed") is False
        and preview.get("projectv2_mutation_performed") is False
        and preview.get("forbidden_fields_untouched") == ["Résumé", "Serveur"]
    )


def _result(
    command: ProjectsCopilotSpecialistIntegratedSmokeCommand,
    *,
    issues: Sequence[str],
    assembly: Mapping[str, Any] | None = None,
    advisory_projection: Mapping[str, Any] | None = None,
    memory: Mapping[str, Any] | None = None,
    publication_preview: Mapping[str, Any] | None = None,
    publication_plan: Mapping[str, Any] | None = None,
    project_fields_preview: Mapping[str, Any] | None = None,
    artifact_correlation_verified: bool = False,
    advisory_context_injected: bool = False,
    source_candidate_injected: bool = False,
    real_memory_closed: bool = False,
    publication_plan_ready: bool = False,
    projects_projection_ready: bool = False,
    integrated_closed_loop_complete: bool = False,
) -> ProjectsCopilotSpecialistIntegratedSmokeResult:
    normalized = _unique_text(issues)
    return ProjectsCopilotSpecialistIntegratedSmokeResult(
        valid=not normalized,
        issues=normalized,
        command=command,
        assembly={} if assembly is None else assembly,
        advisory_projection=(
            {} if advisory_projection is None else advisory_projection
        ),
        memory={} if memory is None else memory,
        publication_preview=(
            {} if publication_preview is None else publication_preview
        ),
        publication_plan={} if publication_plan is None else publication_plan,
        project_fields_preview=(
            {} if project_fields_preview is None else project_fields_preview
        ),
        artifact_correlation_verified=artifact_correlation_verified,
        advisory_context_injected=advisory_context_injected,
        source_candidate_injected=source_candidate_injected,
        real_memory_closed=real_memory_closed,
        publication_plan_ready=publication_plan_ready,
        projects_projection_ready=projects_projection_ready,
        integrated_closed_loop_complete=integrated_closed_loop_complete,
    )


def _mapping(value: object, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProjectsCopilotSpecialistIntegratedSmokeError(
            f"{name} must be a mapping"
        )
    return value


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectsCopilotSpecialistIntegratedSmokeError(
            f"{name} must be non-empty"
        )
    return value.strip()


def _all_strings(value: object) -> tuple[str, ...]:
    values: list[str] = []
    if isinstance(value, str):
        values.append(value)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            values.extend(_all_strings(key))
            values.extend(_all_strings(item))
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        for item in value:
            values.extend(_all_strings(item))
    return tuple(values)


def _first_value_for_key(value: object, key: str) -> str:
    if isinstance(value, Mapping):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate:
            return candidate
        for item in value.values():
            found = _first_value_for_key(item, key)
            if found:
                return found
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        for item in value:
            found = _first_value_for_key(item, key)
            if found:
                return found
    return ""


def _unique_text(values: Sequence[object]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            text
            for value in values
            if (text := str(value).strip())
        )
    )


__all__ = (
    "PROJECTS_COPILOT_SPECIALIST_COMMAND_SCHEMA",
    "PROJECTS_COPILOT_SPECIALIST_INTEGRATED_SMOKE_VERSION",
    "PROJECTS_COPILOT_SPECIALIST_RESULT_SCHEMA",
    "PROJECTS_FIELD_PREVIEW_SCHEMA",
    "ProjectsCopilotSpecialistIntegratedSmokeCommand",
    "ProjectsCopilotSpecialistIntegratedSmokeError",
    "ProjectsCopilotSpecialistIntegratedSmokeResult",
    "run_projects_copilot_specialist_integrated_smoke",
)
