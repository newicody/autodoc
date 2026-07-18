"""Compose the existing r16 GitHub research units into one controlled closed loop.

This is an application composition, not a new orchestrator.  The existing
Scheduler remains the sole task orchestrator and every domain operation is
delegated to the already-installed r16-r7 .. r16-r18 units.

The composition is split deliberately:

1. ``prepare_github_research_love_closed_loop`` performs the local path from a
   correlated GitHub ready_run to a durable final deliverable and a deterministic
   publication plan.  It stops before remote mutation and returns the exact
   digest requiring operator confirmation.
2. ``complete_github_research_love_closed_loop`` consumes that prepared result,
   executes the existing controlled Issue/ProjectV2 publication with the exact
   digest and three locks, then persists the verified publication evidence and
   closes the SQL cycle.

No Scheduler, Dispatcher, EventBus, SQL store, Qdrant client, OpenVINO runtime,
laboratory provider or GitHub transport is constructed here.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from context.github_ready_run_research_admissibility_0287 import (
    GitHubReadyRunArtifactContent,
    GitHubReadyRunResearchAdmissibilityCommand,
    assemble_ready_run_and_evaluate_research_admissibility,
)
from context.github_research_love_final_deliverable_sql_0287 import (
    GitHubResearchLoveFinalDeliverableCommand,
    persist_github_research_love_final_deliverable,
)
from context.github_research_love_final_remote_publication_0287 import (
    GitHubResearchLoveFinalPublicationCommand,
    GitHubResearchLoveFinalPublicationExecution,
    GitHubResearchLoveFinalPublicationPlan,
    build_github_research_love_final_publication_plan,
    execute_github_research_love_final_publication,
)
from context.github_research_love_first_visit_dispatch_0287 import (
    GitHubResearchLoveFirstVisitDispatchCommand,
    dispatch_first_love_visit_from_github_research,
)
from context.github_research_love_liaison_synthesis_0287 import (
    GitHubResearchLoveLiaisonSynthesisCommand,
    build_github_research_love_liaison_synthesis,
)
from context.github_research_love_publication_evidence_sql_0287 import (
    GitHubResearchLovePublicationEvidenceCommand,
    close_github_research_love_cycle,
)
from context.github_research_love_second_visit_dispatch_0287 import (
    GitHubResearchLoveSecondVisitDispatchCommand,
    dispatch_second_love_visit_from_first_analysis,
)
from context.github_research_love_sql_persistence_0287 import (
    persist_github_research_love_analyses,
)
from context.github_research_love_two_analysis_recall_0287 import (
    GitHubResearchLoveTwoAnalysisRecallCommand,
    recall_github_research_love_analyses,
)
from context.github_research_love_two_qdrant_projections_0287 import (
    GitHubResearchLoveTwoProjectionCommand,
    project_github_research_love_analyses,
)
from context.github_research_scheduler_dispatch_0287 import (
    GitHubResearchSchedulerDispatchCommand,
    dispatch_authorized_research_through_existing_scheduler,
)
from context.github_research_scheduler_intake_0287 import (
    GitHubResearchSchedulerIntakeCommand,
    build_authorized_scheduler_intake_for_admissible_research,
)
from context.love_final_deliverable_remote_publication_0287 import (
    FinalDeliverableIssuePublicationPort,
    FinalDeliverableProjectV2PublicationPort,
)
from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)

PREPARED_SCHEMA = "missipy.github.research_love_closed_loop_prepared.v1"
COMPLETED_SCHEMA = "missipy.github.research_love_closed_loop_completed.v1"

_STAGE_ORDER = (
    "ready_run_admissibility",
    "scheduler_intake",
    "scheduler_dispatch",
    "first_specialist",
    "second_specialist",
    "analysis_sql",
    "analysis_qdrant",
    "analysis_recall",
    "liaison_synthesis",
    "final_deliverable_sql",
    "publication_plan",
)


class GitHubResearchLoveCompleteClosedLoopError(RuntimeError):
    """Raised when one existing stage cannot enter the next stage safely."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveClosedLoopPrepareCommand:
    """Inputs for the complete local phase through publication planning."""

    runtime_ports: ImportedActionsRuntimePorts
    ready_run: Mapping[str, Any]
    artifact_contents: tuple[GitHubReadyRunArtifactContent, ...]
    reference_point_reader: Any
    requested_at: str
    analysis_created_at: str
    projected_at: str
    final_created_at: str
    recall_query_text: str
    project_item_id: str
    project_field_ref: str
    project_field_name: str = "Résumé"
    project_status_value: str = "Livrable final prêt"
    publication_policy_decision_id: str = (
        "policy:github-research-love-final-publication"
    )
    conversation_ref: str = ""
    return_route_ref: str = ""
    context_generation: int = 0
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    dense_vector_name: str = "dense_e5_v1"
    sparse_vector_name: str = "sparse_lexical_v1"
    security_scope: str = "security:research-local"
    branch_ref: str = "branch:github-research"
    project_ref: str = "project:github-research"
    first_priority: int = 60
    second_priority: int = 100
    route_timeout_seconds: float = 5.0
    visit_timeout_seconds: float | None = None
    route_request_handler: Callable[[object], object] | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.ready_run, Mapping):
            raise TypeError("ready_run must be a mapping")
        object.__setattr__(
            self,
            "artifact_contents",
            tuple(self.artifact_contents),
        )
        if len(self.artifact_contents) != 3:
            raise GitHubResearchLoveCompleteClosedLoopError(
                "exactly three ready_run artifact contents are required"
            )
        for name in (
            "requested_at",
            "analysis_created_at",
            "projected_at",
            "final_created_at",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
                raise GitHubResearchLoveCompleteClosedLoopError(
                    f"{name} must be a UTC timestamp ending with Z"
                )
        if not self.recall_query_text.strip():
            raise GitHubResearchLoveCompleteClosedLoopError(
                "recall_query_text must not be empty"
            )
        for name in (
            "project_item_id",
            "project_field_ref",
            "project_field_name",
            "project_status_value",
            "publication_policy_decision_id",
            "dense_vector_name",
            "sparse_vector_name",
            "security_scope",
            "branch_ref",
            "project_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise GitHubResearchLoveCompleteClosedLoopError(
                    f"{name} must not be empty"
                )
            object.__setattr__(self, name, value.strip())
        if not self.publication_policy_decision_id.startswith("policy:"):
            raise GitHubResearchLoveCompleteClosedLoopError(
                "publication_policy_decision_id must start with policy:"
            )
        if self.dense_vector_name == self.sparse_vector_name:
            raise GitHubResearchLoveCompleteClosedLoopError(
                "dense and sparse vector names must differ"
            )
        if (
            isinstance(self.context_generation, bool)
            or not isinstance(self.context_generation, int)
            or self.context_generation < 0
        ):
            raise GitHubResearchLoveCompleteClosedLoopError(
                "context_generation must be a non-negative integer"
            )
        if self.route_request_handler is not None and not callable(
            self.route_request_handler
        ):
            raise TypeError("route_request_handler must be callable")


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveClosedLoopPrepared:
    """Local phase result retaining typed stage values only in memory."""

    schema: str
    valid: bool
    status: str
    issues: tuple[str, ...]
    failed_stage: str = ""
    repository: str = ""
    issue_number: int = 0
    work_package_ref: str = ""
    stage_results: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != PREPARED_SCHEMA:
            raise GitHubResearchLoveCompleteClosedLoopError(
                "unsupported prepared closed-loop schema"
            )
        frozen = dict(self.stage_results)
        unknown = set(frozen) - set(_STAGE_ORDER)
        if unknown:
            raise GitHubResearchLoveCompleteClosedLoopError(
                "unknown prepared stages: " + ", ".join(sorted(unknown))
            )
        object.__setattr__(
            self,
            "stage_results",
            MappingProxyType(frozen),
        )
        if self.valid:
            if self.status != "publication-confirmation-required":
                raise GitHubResearchLoveCompleteClosedLoopError(
                    "valid prepared result must require publication confirmation"
                )
            if tuple(frozen) != _STAGE_ORDER:
                raise GitHubResearchLoveCompleteClosedLoopError(
                    "valid prepared result must contain every stage in order"
                )
            if not self.repository or self.issue_number <= 0:
                raise GitHubResearchLoveCompleteClosedLoopError(
                    "valid prepared result requires repository and issue number"
                )
            if not self.work_package_ref.startswith("research-work-package:"):
                raise GitHubResearchLoveCompleteClosedLoopError(
                    "valid prepared result requires a work package reference"
                )
            if self.failed_stage:
                raise GitHubResearchLoveCompleteClosedLoopError(
                    "valid prepared result cannot have failed_stage"
                )

    @property
    def publication_plan(self) -> GitHubResearchLoveFinalPublicationPlan:
        value = self.stage_results.get("publication_plan")
        plan_digest = getattr(value, "plan_digest", None)
        to_mapping = getattr(value, "to_mapping", None)
        if not isinstance(value, GitHubResearchLoveFinalPublicationPlan) and (
            not isinstance(plan_digest, str)
            or not plan_digest.startswith("sha256:")
            or not callable(to_mapping)
        ):
            raise GitHubResearchLoveCompleteClosedLoopError(
                "prepared publication plan is unavailable"
            )
        return value  # type: ignore[return-value]

    def stage(self, name: str) -> object:
        if name not in self.stage_results:
            raise GitHubResearchLoveCompleteClosedLoopError(
                f"prepared stage is unavailable: {name}"
            )
        return self.stage_results[name]

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "failed_stage": self.failed_stage,
            "repository": self.repository,
            "issue_number": self.issue_number,
            "work_package_ref": self.work_package_ref,
            "stage_order": list(self.stage_results),
            "stages": {
                name: _to_mapping(value)
                for name, value in self.stage_results.items()
            },
            "publication_plan_digest": (
                self.publication_plan.plan_digest if self.valid else ""
            ),
            "boundaries": {
                "application_composition_only": True,
                "scheduler_remains_sole_orchestrator": True,
                "existing_runtime_ports_reused": True,
                "new_scheduler_created": False,
                "new_dispatcher_created": False,
                "new_eventbus_created": False,
                "new_sql_store_created": False,
                "new_qdrant_client_created": False,
                "new_openvino_runtime_created": False,
                "new_github_transport_created": False,
                "remote_publication_performed": False,
                "cycle_closed": False,
                "operator_confirmation_required": self.valid,
            },
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveClosedLoopCompleteCommand:
    """Explicit remote confirmation and durable closure request."""

    runtime_ports: ImportedActionsRuntimePorts
    prepared: GitHubResearchLoveClosedLoopPrepared
    confirm_plan_digest: str
    closed_at: str
    operator_decision: str = "approve"
    remote_mutation_allowed: bool = False
    issue_publication_allowed: bool = False
    project_projection_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(
            self.prepared,
            GitHubResearchLoveClosedLoopPrepared,
        ):
            raise TypeError(
                "prepared must be GitHubResearchLoveClosedLoopPrepared"
            )
        if not self.prepared.valid:
            raise GitHubResearchLoveCompleteClosedLoopError(
                "prepared closed loop must be valid"
            )
        if self.operator_decision != "approve":
            raise GitHubResearchLoveCompleteClosedLoopError(
                "operator_decision must be approve"
            )
        if not self.confirm_plan_digest.startswith("sha256:"):
            raise GitHubResearchLoveCompleteClosedLoopError(
                "confirm_plan_digest must be sha256:*"
            )
        if "T" not in self.closed_at or not self.closed_at.endswith("Z"):
            raise GitHubResearchLoveCompleteClosedLoopError(
                "closed_at must be a UTC timestamp ending with Z"
            )


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveClosedLoopCompleted:
    """Remote publication and SQL closure result."""

    schema: str
    valid: bool
    status: str
    issues: tuple[str, ...]
    prepared: GitHubResearchLoveClosedLoopPrepared
    remote_publication: object | None = None
    closure: object | None = None

    def __post_init__(self) -> None:
        if self.schema != COMPLETED_SCHEMA:
            raise GitHubResearchLoveCompleteClosedLoopError(
                "unsupported completed closed-loop schema"
            )
        if self.valid:
            if self.status != "closed":
                raise GitHubResearchLoveCompleteClosedLoopError(
                    "valid completed status must be closed"
                )
            if self.remote_publication is None or self.closure is None:
                raise GitHubResearchLoveCompleteClosedLoopError(
                    "valid completion requires publication and closure"
                )

    def to_mapping(self) -> dict[str, object]:
        remote = _to_mapping(self.remote_publication)
        closure = _to_mapping(self.closure)
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "prepared": self.prepared.to_mapping(),
            "remote_publication": remote,
            "closure": closure,
            "cycle_closed": bool(
                self.valid
                and isinstance(closure, Mapping)
                and closure.get("cycle_closed") is True
            ),
            "boundaries": {
                "remote_publication_executed_once": self.remote_publication
                is not None,
                "publication_evidence_persisted": self.closure is not None,
                "scheduler_remains_sole_orchestrator": True,
                "new_orchestrator_created": False,
                "new_scheduler_created": False,
                "remote_publication_reexecuted_by_closure": False,
            },
        }


async def prepare_github_research_love_closed_loop(
    command: GitHubResearchLoveClosedLoopPrepareCommand,
) -> GitHubResearchLoveClosedLoopPrepared:
    """Run r16-r7 through r16-r17 planning and stop at the digest boundary."""

    stages: dict[str, object] = {}
    repository = ""
    issue_number = 0
    work_package_ref = ""

    try:
        ports = validate_imported_actions_runtime_ports(
            command.runtime_ports
        )
        ready = assemble_ready_run_and_evaluate_research_admissibility(
            GitHubReadyRunResearchAdmissibilityCommand(
                ready_run=command.ready_run,
                artifact_contents=command.artifact_contents,
                conversation_ref=command.conversation_ref,
                return_route_ref=command.return_route_ref,
                context_generation=command.context_generation,
                context_refs=command.context_refs,
                evidence_refs=command.evidence_refs,
            )
        )
        stages["ready_run_admissibility"] = ready
        if not ready.valid or not ready.admissible:
            return _prepare_failure(
                stages,
                "ready_run_admissibility",
                ready.issues,
            )

        work_package_build = _required_mapping(
            ready.work_package_build,
            "work_package",
        )
        work_package = dict(work_package_build)
        admissibility = _required_mapping(
            ready.admissibility,
            "route_candidate",
        )
        repository = _required_text(work_package, "repository")
        work_package_ref = _required_text(
            work_package,
            "work_package_ref",
        )
        source_issue = _required_mapping(work_package, "source_issue")
        issue_number = _positive_int(source_issue, "number")

        intake = build_authorized_scheduler_intake_for_admissible_research(
            GitHubResearchSchedulerIntakeCommand(
                route_candidate=admissibility,
                requested_at=command.requested_at,
            )
        )
        stages["scheduler_intake"] = intake
        if not intake.valid or not intake.authorized:
            return _prepare_failure(
                stages,
                "scheduler_intake",
                intake.issues,
                repository=repository,
                issue_number=issue_number,
                work_package_ref=work_package_ref,
            )

        scheduler_dispatch = (
            await dispatch_authorized_research_through_existing_scheduler(
                GitHubResearchSchedulerDispatchCommand(
                    runtime_ports=ports,
                    scheduler_intake=intake.to_mapping(),
                    timeout_seconds=command.route_timeout_seconds,
                    priority=command.first_priority,
                    route_request_handler=command.route_request_handler,
                )
            )
        )
        stages["scheduler_dispatch"] = scheduler_dispatch
        if not scheduler_dispatch.valid:
            return _prepare_failure(
                stages,
                "scheduler_dispatch",
                scheduler_dispatch.issues,
                repository=repository,
                issue_number=issue_number,
                work_package_ref=work_package_ref,
            )

        first = await dispatch_first_love_visit_from_github_research(
            GitHubResearchLoveFirstVisitDispatchCommand(
                runtime_ports=ports,
                work_package=work_package,
                scheduler_intake=intake.to_mapping(),
                scheduler_dispatch=scheduler_dispatch.to_mapping(),
                priority=command.first_priority,
                timeout_seconds=command.visit_timeout_seconds,
            )
        )
        stages["first_specialist"] = first
        if not first.valid:
            return _prepare_failure(
                stages,
                "first_specialist",
                first.issues,
                repository=repository,
                issue_number=issue_number,
                work_package_ref=work_package_ref,
            )

        second = await dispatch_second_love_visit_from_first_analysis(
            GitHubResearchLoveSecondVisitDispatchCommand(
                runtime_ports=ports,
                first_dispatch=first,
                priority=command.second_priority,
                timeout_seconds=command.visit_timeout_seconds,
            )
        )
        stages["second_specialist"] = second
        if not second.valid:
            return _prepare_failure(
                stages,
                "second_specialist",
                second.issues,
                repository=repository,
                issue_number=issue_number,
                work_package_ref=work_package_ref,
            )

        analysis_sql = persist_github_research_love_analyses(
            runtime_ports=ports,
            first_dispatch=first.to_mapping(),
            second_dispatch=second.to_mapping(),
            created_at=command.analysis_created_at,
        )
        stages["analysis_sql"] = analysis_sql
        if not analysis_sql.valid:
            return _prepare_failure(
                stages,
                "analysis_sql",
                analysis_sql.issues,
                repository=repository,
                issue_number=issue_number,
                work_package_ref=work_package_ref,
            )

        projections = await project_github_research_love_analyses(
            GitHubResearchLoveTwoProjectionCommand(
                runtime_ports=ports,
                sql_persistence=analysis_sql.to_mapping(),
                reference_point_reader=command.reference_point_reader,
                branch_ref=command.branch_ref,
                project_ref=command.project_ref,
                conversation_ref=(
                    command.conversation_ref
                    or f"conversation:github-research-{issue_number}"
                ),
                security_scope=command.security_scope,
                dense_vector_name=command.dense_vector_name,
                sparse_vector_name=command.sparse_vector_name,
                projected_at=command.projected_at,
                allow_write=True,
            )
        )
        stages["analysis_qdrant"] = projections
        if not projections.valid:
            return _prepare_failure(
                stages,
                "analysis_qdrant",
                projections.issues,
                repository=repository,
                issue_number=issue_number,
                work_package_ref=work_package_ref,
            )

        recall = await recall_github_research_love_analyses(
            GitHubResearchLoveTwoAnalysisRecallCommand(
                runtime_ports=ports,
                sql_persistence=analysis_sql.to_mapping(),
                two_projections=projections.to_mapping(),
                query_text=command.recall_query_text,
            )
        )
        stages["analysis_recall"] = recall
        if not recall.valid:
            return _prepare_failure(
                stages,
                "analysis_recall",
                recall.issues,
                repository=repository,
                issue_number=issue_number,
                work_package_ref=work_package_ref,
            )

        liaison = build_github_research_love_liaison_synthesis(
            GitHubResearchLoveLiaisonSynthesisCommand(
                recall=recall,
            )
        )
        stages["liaison_synthesis"] = liaison
        if not liaison.valid:
            return _prepare_failure(
                stages,
                "liaison_synthesis",
                liaison.issues,
                repository=repository,
                issue_number=issue_number,
                work_package_ref=work_package_ref,
            )

        final_deliverable = persist_github_research_love_final_deliverable(
            GitHubResearchLoveFinalDeliverableCommand(
                runtime_ports=ports,
                liaison=liaison,
                analysis_sql_persistence=analysis_sql.to_mapping(),
                target_ref=f"github:{repository}#{issue_number}",
                created_at=command.final_created_at,
            )
        )
        stages["final_deliverable_sql"] = final_deliverable
        if not final_deliverable.valid:
            return _prepare_failure(
                stages,
                "final_deliverable_sql",
                final_deliverable.issues,
                repository=repository,
                issue_number=issue_number,
                work_package_ref=work_package_ref,
            )

        publication_plan = (
            build_github_research_love_final_publication_plan(
                GitHubResearchLoveFinalPublicationCommand(
                    final_deliverable=final_deliverable.to_mapping(),
                    liaison=liaison.to_mapping(),
                    repository=repository,
                    issue_number=issue_number,
                    source_issue_ref=(
                        f"github-frame:{repository}/issues/{issue_number}"
                    ),
                    policy_decision_id=(
                        command.publication_policy_decision_id
                    ),
                    operator_decision="approve",
                    project_item_id=command.project_item_id,
                    project_field_ref=command.project_field_ref,
                    project_field_name=command.project_field_name,
                    project_status_value=command.project_status_value,
                )
            )
        )
        stages["publication_plan"] = publication_plan

        return GitHubResearchLoveClosedLoopPrepared(
            schema=PREPARED_SCHEMA,
            valid=True,
            status="publication-confirmation-required",
            issues=(),
            repository=repository,
            issue_number=issue_number,
            work_package_ref=work_package_ref,
            stage_results=stages,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return _prepare_failure(
            stages,
            _next_stage_name(stages),
            (f"{type(exc).__name__}: {exc}",),
            repository=repository,
            issue_number=issue_number,
            work_package_ref=work_package_ref,
        )


def complete_github_research_love_closed_loop(
    command: GitHubResearchLoveClosedLoopCompleteCommand,
    *,
    issue_port: FinalDeliverableIssuePublicationPort,
    project_port: FinalDeliverableProjectV2PublicationPort,
) -> GitHubResearchLoveClosedLoopCompleted:
    """Execute the confirmed remote boundary once, then close the SQL cycle."""

    try:
        ports = validate_imported_actions_runtime_ports(
            command.runtime_ports
        )
        remote = execute_github_research_love_final_publication(
            GitHubResearchLoveFinalPublicationExecution(
                plan=command.prepared.publication_plan,
                operator_decision=command.operator_decision,
                execute=True,
                confirm_plan_digest=command.confirm_plan_digest,
                remote_mutation_allowed=command.remote_mutation_allowed,
                issue_publication_allowed=command.issue_publication_allowed,
                project_projection_allowed=command.project_projection_allowed,
            ),
            issue_port=issue_port,
            project_port=project_port,
        )
        if not remote.valid or remote.status not in {
            "published",
            "published-replay",
        }:
            return GitHubResearchLoveClosedLoopCompleted(
                schema=COMPLETED_SCHEMA,
                valid=False,
                status="remote-publication-failed",
                issues=tuple(remote.remote_result.issues),
                prepared=command.prepared,
                remote_publication=remote,
            )

        final_deliverable = command.prepared.stage(
            "final_deliverable_sql"
        )
        closure = close_github_research_love_cycle(
            GitHubResearchLovePublicationEvidenceCommand(
                runtime_ports=ports,
                final_deliverable=_to_mapping(final_deliverable),
                remote_publication=remote.to_mapping(),
                closed_at=command.closed_at,
            )
        )
        if not closure.valid:
            return GitHubResearchLoveClosedLoopCompleted(
                schema=COMPLETED_SCHEMA,
                valid=False,
                status="closure-failed",
                issues=tuple(closure.issues),
                prepared=command.prepared,
                remote_publication=remote,
                closure=closure,
            )
        return GitHubResearchLoveClosedLoopCompleted(
            schema=COMPLETED_SCHEMA,
            valid=True,
            status="closed",
            issues=(),
            prepared=command.prepared,
            remote_publication=remote,
            closure=closure,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return GitHubResearchLoveClosedLoopCompleted(
            schema=COMPLETED_SCHEMA,
            valid=False,
            status="failed",
            issues=(f"{type(exc).__name__}: {exc}",),
            prepared=command.prepared,
        )


def _prepare_failure(
    stages: Mapping[str, object],
    failed_stage: str,
    issues: object,
    *,
    repository: str = "",
    issue_number: int = 0,
    work_package_ref: str = "",
) -> GitHubResearchLoveClosedLoopPrepared:
    normalized_issues = _issues(issues)
    return GitHubResearchLoveClosedLoopPrepared(
        schema=PREPARED_SCHEMA,
        valid=False,
        status="failed",
        issues=normalized_issues or ("stage failed without issue detail",),
        failed_stage=failed_stage,
        repository=repository,
        issue_number=issue_number,
        work_package_ref=work_package_ref,
        stage_results=dict(stages),
    )


def _next_stage_name(stages: Mapping[str, object]) -> str:
    for name in _STAGE_ORDER:
        if name not in stages:
            return name
    return "publication_plan"


def _issues(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple)):
        return tuple(
            dict.fromkeys(str(item) for item in value if str(item))
        )
    return (str(value),) if value is not None else ()


def _to_mapping(value: object | None) -> dict[str, Any]:
    if value is None:
        return {}
    method = getattr(value, "to_mapping", None)
    if callable(method):
        mapping = method()
        if not isinstance(mapping, Mapping):
            raise GitHubResearchLoveCompleteClosedLoopError(
                "stage to_mapping() must return a mapping"
            )
        return dict(mapping)
    if isinstance(value, Mapping):
        return dict(value)
    raise GitHubResearchLoveCompleteClosedLoopError(
        f"stage result is not serializable: {type(value).__name__}"
    )


def _required_mapping(
    value: Mapping[str, Any],
    name: str,
) -> Mapping[str, Any]:
    candidate = value.get(name)
    if not isinstance(candidate, Mapping):
        raise GitHubResearchLoveCompleteClosedLoopError(
            f"{name} must be an object"
        )
    return candidate


def _required_text(
    value: Mapping[str, Any],
    name: str,
) -> str:
    candidate = value.get(name)
    if not isinstance(candidate, str) or not candidate.strip():
        raise GitHubResearchLoveCompleteClosedLoopError(
            f"{name} must not be empty"
        )
    return candidate.strip()


def _positive_int(
    value: Mapping[str, Any],
    name: str,
) -> int:
    candidate = value.get(name)
    if (
        isinstance(candidate, bool)
        or not isinstance(candidate, int)
        or candidate <= 0
    ):
        raise GitHubResearchLoveCompleteClosedLoopError(
            f"{name} must be a positive integer"
        )
    return candidate


__all__ = (
    "COMPLETED_SCHEMA",
    "GitHubResearchLoveClosedLoopCompleteCommand",
    "GitHubResearchLoveClosedLoopCompleted",
    "GitHubResearchLoveClosedLoopPrepareCommand",
    "GitHubResearchLoveClosedLoopPrepared",
    "GitHubResearchLoveCompleteClosedLoopError",
    "PREPARED_SCHEMA",
    "complete_github_research_love_closed_loop",
    "prepare_github_research_love_closed_loop",
)
