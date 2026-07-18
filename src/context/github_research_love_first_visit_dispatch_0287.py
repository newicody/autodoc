"""Dispatch the first native love-specialist visit through the existing Scheduler.

The GitHub research path has already produced:
- one correlated research work package;
- one authorized Scheduler intake;
- one successful Scheduler route reply.

This unit converts those proofs into the first concrete love-study visit,
registers or reuses one append-only collaborative provider on the existing
Dispatcher, and submits the visit with the existing Scheduler binding.

It does not call a specialist directly, create or start a Scheduler, create a
parallel Dispatcher/EventBus, persist SQL/Qdrant data, synthesize both analyses,
or mutate GitHub.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
from typing import Any

from context.correlated_research_work_package_0287 import WORK_PACKAGE_SCHEMA
from context.github_research_scheduler_dispatch_0287 import (
    SCHEMA as SCHEDULER_DISPATCH_SCHEMA,
)
from context.github_research_scheduler_intake_0287 import (
    SCHEMA as SCHEDULER_INTAKE_SCHEMA,
)
from context.laboratory_framework_contract_0273 import (
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
)
from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)
from context.love_study_contracts_0287 import (
    LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
    LOVE_STUDY_REQUEST_CONTRACT_REF,
    LOVE_STUDY_REQUEST_SCHEMA,
    LoveStudyRequest,
)
from context.native_love_laboratory_collaboration_scheduler_binding_0287 import (
    NativeLoveCollaborativeVisitRequestHandler,
    NativeLoveCollaborationSchedulerVisitReceipt,
    register_native_love_collaboration_visit_handler,
    submit_native_love_collaboration_visit,
)
from context.native_love_laboratory_second_specialist_0287 import (
    InMemoryCollaborativeLoveLaboratoryInputResolver,
    NativeLoveCollaborationError,
    build_native_love_collaborative_provider,
)
from context.specialist_multitask_model_0287 import (
    SPECIALIST_TASK_REQUEST_SCHEMA,
    SpecialistTaskRequest,
)
from contracts.event import EventType

SCHEMA = "missipy.github.research_love_first_visit_dispatch.v1"
_ALLOWED_REPOSITORY = "newicody/projects"


class GitHubResearchLoveFirstVisitDispatchError(RuntimeError):
    """Raised when the existing laboratory handler cannot be safely reused."""


class GitHubResearchLoveRuntimeResolver(
    InMemoryCollaborativeLoveLaboratoryInputResolver
):
    """Append-only multi-research resolver owned by the existing runtime.

    The historical resolver already supports append-only tasks and first
    analyses.  This subclass adds the missing append-only study registration so
    one Dispatcher handler can serve several GitHub research Issues without
    replacing the provider between visits.
    """

    def register_study(self, study: LoveStudyRequest) -> None:
        if not isinstance(study, LoveStudyRequest):
            raise TypeError("study must be LoveStudyRequest")
        existing = self._studies.get(study.study_ref)
        if existing is not None and existing != study:
            raise NativeLoveCollaborationError(
                "study_ref collision in GitHub research resolver"
            )
        self._studies[study.study_ref] = study


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFirstVisitDispatchCommand:
    """One bounded first-visit request against an injected live runtime."""

    runtime_ports: ImportedActionsRuntimePorts
    work_package: Mapping[str, Any]
    scheduler_intake: Mapping[str, Any]
    scheduler_dispatch: Mapping[str, Any]
    priority: int = 60
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        for name in ("work_package", "scheduler_intake", "scheduler_dispatch"):
            if not isinstance(getattr(self, name), Mapping):
                raise TypeError(f"{name} must be a mapping")
        if (
            isinstance(self.priority, bool)
            or not isinstance(self.priority, int)
            or self.priority < -1_000
            or self.priority > 1_000_000
        ):
            raise ValueError("priority is outside the Scheduler policy range")
        if (
            self.timeout_seconds is not None
            and (
                isinstance(self.timeout_seconds, bool)
                or self.timeout_seconds <= 0
            )
        ):
            raise ValueError("timeout_seconds must be > 0 when provided")


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFirstVisitSurface:
    """Typed study, first task and visit derived from authoritative content."""

    study: LoveStudyRequest
    first_task: SpecialistTaskRequest
    first_visit: LaboratoryVisitRequest

    def to_mapping(self) -> dict[str, Any]:
        return {
            "study": self.study.to_mapping(),
            "first_task": self.first_task.to_mapping(),
            "first_visit": self.first_visit.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveFirstVisitDispatchResult:
    """Proof that the first specialist executed through the Scheduler path."""

    valid: bool
    status: str
    issues: tuple[str, ...]
    handler_action: str = ""
    work_package_ref: str = ""
    route_request_id: str = ""
    route_event_id: str = ""
    surface: GitHubResearchLoveFirstVisitSurface | None = None
    scheduler_receipt: Mapping[str, Any] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, Any]:
        execution = self.scheduler_receipt.get("execution")
        execution = execution if isinstance(execution, Mapping) else {}
        result = execution.get("result")
        result = result if isinstance(result, Mapping) else {}
        return {
            "schema": SCHEMA,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "handler_action": self.handler_action,
            "work_package_ref": self.work_package_ref,
            "route_request_id": self.route_request_id,
            "route_event_id": self.route_event_id,
            "surface": (
                self.surface.to_mapping() if self.surface is not None else None
            ),
            "scheduler_receipt": dict(self.scheduler_receipt),
            "first_analysis_result": dict(result),
            "existing_scheduler_reused": True,
            "existing_dispatcher_reused": True,
            "existing_laboratory_handler_reused": True,
            "append_only_multi_research_resolver": True,
            "scheduler_created": False,
            "scheduler_started": False,
            "parallel_dispatcher_created": False,
            "parallel_eventbus_created": False,
            "direct_specialist_invocation": False,
            "laboratory_execution_started": bool(self.scheduler_receipt),
            "laboratory_execution_completed": self.valid,
            "first_specialist_execution_started": bool(self.scheduler_receipt),
            "first_specialist_execution_completed": self.valid,
            "second_specialist_execution_started": False,
            "global_synthesis_created": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
        }


def build_first_love_visit_surface_from_github_research(
    *,
    runtime_ports: ImportedActionsRuntimePorts,
    work_package: Mapping[str, Any],
    scheduler_intake: Mapping[str, Any],
    scheduler_dispatch: Mapping[str, Any],
) -> GitHubResearchLoveFirstVisitSurface:
    """Build the first specialist surface from authoritative request content."""

    ports = validate_imported_actions_runtime_ports(runtime_ports)
    issues = _validate_inputs(
        work_package=work_package,
        scheduler_intake=scheduler_intake,
        scheduler_dispatch=scheduler_dispatch,
    )
    if issues:
        raise GitHubResearchLoveFirstVisitDispatchError("; ".join(issues))

    candidate = _mapping(scheduler_intake["research_route_candidate"])
    request = _mapping(work_package["authoritative_request"])
    issue = _mapping(work_package["source_issue"])
    issue_number = int(issue["number"])
    work_package_ref = _text(work_package["work_package_ref"])
    suffix = hashlib.sha256(work_package_ref.encode("utf-8")).hexdigest()[:16]

    title = _require_text("authoritative request title", request.get("title"))
    body = _require_text("authoritative request body", request.get("body"))
    study_ref = f"love-study:github-{issue_number}-{suffix}"
    task_ref = f"specialist-task:love-first-{suffix}"
    conversation_ref = f"laboratory-conversation:github-research-{suffix}"
    return_route_ref = f"route:github-research-{suffix}"
    context_refs = (f"ctx:github-research-{suffix}",)
    evidence_refs = _evidence_refs(
        suffix=suffix,
        advisory_present=bool(work_package.get("advisory_present")),
    )

    study = LoveStudyRequest(
        schema=LOVE_STUDY_REQUEST_SCHEMA,
        study_ref=study_ref,
        source_issue_ref=(
            f"github-issue:{work_package['repository']}#{issue_number}"
        ),
        objective=title,
        subject_text=body,
        constraints=(
            "Ne pas produire de diagnostic psychologique.",
            "Conserver les contradictions et incertitudes.",
            "La demande GitHub reste l'autorité.",
        ),
        success_criteria=(
            "Produire une analyse conceptuelle et affective attribuée.",
            "Fonder les constats sur des éléments observables du texte source.",
        ),
        context_refs=context_refs,
        evidence_refs=evidence_refs,
        metadata={
            "repository": work_package["repository"],
            "run_id": work_package["run_id"],
            "work_package_ref": work_package_ref,
            "route_candidate_ref": candidate["route_candidate_ref"],
            "request_authoritative": True,
            "advisory_used_as_hint_only": True,
        },
    )
    first_task = SpecialistTaskRequest(
        schema=SPECIALIST_TASK_REQUEST_SCHEMA,
        task_ref=task_ref,
        plan_ref=f"specialist-task-plan:love-{suffix}",
        mission_ref=f"mission:love-study-{issue_number}-{suffix}",
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        task_type_ref="task-type:love.concept_analysis",
        capability="love.concept_analysis",
        objective="Analyser profondément les concepts et affects présents.",
        input_contract_ref=LOVE_STUDY_REQUEST_CONTRACT_REF,
        expected_output_contract_ref=LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
        conversation_ref=conversation_ref,
        return_route_ref=return_route_ref,
        constraints=study.constraints,
        success_criteria=(
            "Fournir des constats attribués et leurs preuves.",
        ),
        context_refs=context_refs,
        evidence_refs=evidence_refs,
        priority=60,
        idempotency_key=f"idempotency:github-love-first-{suffix}",
        metadata={
            "context_revision_ref": ports.base_revision_ref,
            "work_package_ref": work_package_ref,
            "source_candidate_ref": work_package["source_candidate_ref"],
            "route_request_id": _mapping(
                scheduler_intake["scheduler_route_request"]
            )["request_id"],
            "route_event_id": scheduler_dispatch["event_id"],
            "request_authoritative": True,
            "advisory_used_as_hint_only": True,
        },
    )
    first_visit = LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref=f"laboratory-visit:love-first-{suffix}",
        laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        objective_ref=first_task.task_ref,
        source_candidate_ref=study.study_ref,
        context_generation=int(work_package["context_generation"]),
        input_contract_ref=first_task.input_contract_ref,
        expected_output_contract_ref=first_task.expected_output_contract_ref,
        resource_budget=LaboratoryResourceBudget(),
        return_route_ref=first_task.return_route_ref,
        context_refs=first_task.context_refs,
        evidence_refs=first_task.evidence_refs,
        origin_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        target_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        conversation_ref=first_task.conversation_ref,
        metadata=(
            ("repository", _ALLOWED_REPOSITORY),
            ("run_id", _text(work_package["run_id"])),
            ("work_package_ref", work_package_ref),
            ("request_authoritative", "true"),
            ("advisory_used_as_hint_only", "true"),
        ),
    )
    return GitHubResearchLoveFirstVisitSurface(
        study=study,
        first_task=first_task,
        first_visit=first_visit,
    )


async def dispatch_first_love_visit_from_github_research(
    command: GitHubResearchLoveFirstVisitDispatchCommand,
) -> GitHubResearchLoveFirstVisitDispatchResult:
    """Register/reuse the provider and execute the first visit via Scheduler."""

    try:
        ports = validate_imported_actions_runtime_ports(command.runtime_ports)
        surface = build_first_love_visit_surface_from_github_research(
            runtime_ports=ports,
            work_package=command.work_package,
            scheduler_intake=command.scheduler_intake,
            scheduler_dispatch=command.scheduler_dispatch,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return _invalid("rejected", (str(exc),))

    running = getattr(ports.scheduler, "running", None)
    if running is False:
        return _invalid(
            "scheduler-not-running",
            (
                "the existing Scheduler must already be running; "
                "r16-r10 will not start another Scheduler",
            ),
            surface=surface,
        )

    try:
        handler_action = _register_or_reuse_handler(
            ports.dispatcher,
            study=surface.study,
            first_task=surface.first_task,
        )
        receipt = await submit_native_love_collaboration_visit(
            ports.scheduler,
            surface.first_visit,
            priority=command.priority,
            timeout=command.timeout_seconds,
            source="github.research.love-first-visit",
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        return _invalid(
            "laboratory-visit-failed",
            (f"{type(exc).__name__}: {exc}",),
            surface=surface,
        )

    receipt_mapping = receipt.to_mapping()
    execution = receipt_mapping.get("execution")
    execution = execution if isinstance(execution, Mapping) else {}
    if execution.get("specialist_stage") != "first_analysis":
        return _invalid(
            "first-analysis-invalid",
            ("laboratory receipt is not a first-specialist analysis",),
            surface=surface,
            handler_action=handler_action,
            scheduler_receipt=receipt_mapping,
        )
    if execution.get("result_valid") is not True:
        return _invalid(
            "first-analysis-invalid",
            tuple(
                str(item)
                for item in execution.get("validation_issues", ())
            )
            or ("first-specialist result is invalid",),
            surface=surface,
            handler_action=handler_action,
            scheduler_receipt=receipt_mapping,
        )

    intake_route = _mapping(command.scheduler_intake["scheduler_route_request"])
    return GitHubResearchLoveFirstVisitDispatchResult(
        valid=True,
        status="first-specialist-completed",
        issues=(),
        handler_action=handler_action,
        work_package_ref=_text(command.work_package["work_package_ref"]),
        route_request_id=_text(intake_route["request_id"]),
        route_event_id=_text(command.scheduler_dispatch["event_id"]),
        surface=surface,
        scheduler_receipt=receipt_mapping,
    )


def _register_or_reuse_handler(
    dispatcher: Any,
    *,
    study: LoveStudyRequest,
    first_task: SpecialistTaskRequest,
) -> str:
    handlers = getattr(dispatcher, "handlers", None)
    current = (
        handlers.get(EventType.LABORATORY_VISIT_REQUEST)
        if isinstance(handlers, Mapping)
        else None
    )
    if current is None:
        resolver = GitHubResearchLoveRuntimeResolver(
            studies={study.study_ref: study},
            tasks={first_task.task_ref: first_task},
        )
        provider = build_native_love_collaborative_provider(resolver)
        register_native_love_collaboration_visit_handler(
            dispatcher,
            provider=provider,
        )
        return "registered"

    if not isinstance(current, NativeLoveCollaborativeVisitRequestHandler):
        raise GitHubResearchLoveFirstVisitDispatchError(
            "LABORATORY_VISIT_REQUEST already has a different handler"
        )
    resolver = current.provider.resolver
    if not isinstance(resolver, GitHubResearchLoveRuntimeResolver):
        raise GitHubResearchLoveFirstVisitDispatchError(
            "existing love handler does not own the multi-research resolver"
        )
    resolver.register_study(study)
    resolver.register_task(first_task)
    return "replay"


def _validate_inputs(
    *,
    work_package: Mapping[str, Any],
    scheduler_intake: Mapping[str, Any],
    scheduler_dispatch: Mapping[str, Any],
) -> list[str]:
    issues: list[str] = []
    if work_package.get("schema") != WORK_PACKAGE_SCHEMA:
        issues.append("unsupported correlated work package schema")
    if work_package.get("repository") != _ALLOWED_REPOSITORY:
        issues.append("work package repository is not newicody/projects")
    if work_package.get("request_authoritative") is not True:
        issues.append("work package must keep the request authoritative")
    if work_package.get("advisory_used_as_hint_only") is not True:
        issues.append("Copilot advisory must remain hint-only")
    if work_package.get("advisory_present") is not True:
        issues.append("the first Copilot advisory must be present")

    if scheduler_intake.get("schema") != SCHEDULER_INTAKE_SCHEMA:
        issues.append("unsupported Scheduler intake schema")
    if scheduler_intake.get("valid") is not True:
        issues.append("Scheduler intake must be valid")
    if scheduler_intake.get("authorized") is not True:
        issues.append("Scheduler intake must be authorized")
    if scheduler_intake.get("status") != "scheduler-request-ready":
        issues.append("Scheduler intake is not ready")

    if scheduler_dispatch.get("schema") != SCHEDULER_DISPATCH_SCHEMA:
        issues.append("unsupported Scheduler dispatch schema")
    if scheduler_dispatch.get("valid") is not True:
        issues.append("Scheduler route dispatch must be valid")
    if scheduler_dispatch.get("status") != "route-ready":
        issues.append("Scheduler route is not ready")
    if scheduler_dispatch.get("laboratory_execution_started") is not False:
        issues.append("laboratory execution has already started")

    candidate = _mapping(scheduler_intake.get("research_route_candidate"))
    route = _mapping(scheduler_intake.get("scheduler_route_request"))
    reply = _mapping(scheduler_dispatch.get("route_reply"))
    issue = _mapping(work_package.get("source_issue"))

    for name, value in (
        ("work_package_ref", work_package.get("work_package_ref")),
        ("run_id", work_package.get("run_id")),
        ("source_candidate_ref", work_package.get("source_candidate_ref")),
        ("route_candidate_ref", candidate.get("route_candidate_ref")),
        ("request_id", route.get("request_id")),
        ("route_event_id", scheduler_dispatch.get("event_id")),
    ):
        if not _text(value):
            issues.append(f"{name} must not be empty")

    if candidate.get("work_package_ref") != work_package.get("work_package_ref"):
        issues.append("route candidate work_package_ref mismatch")
    if candidate.get("repository") != work_package.get("repository"):
        issues.append("route candidate repository mismatch")
    if candidate.get("run_id") != work_package.get("run_id"):
        issues.append("route candidate run_id mismatch")
    if candidate.get("issue_number") != issue.get("number"):
        issues.append("route candidate issue_number mismatch")
    if candidate.get("source_candidate_ref") not in (
        None,
        work_package.get("source_candidate_ref"),
    ):
        issues.append("route candidate source_candidate_ref mismatch")

    if scheduler_dispatch.get("request_id") != route.get("request_id"):
        issues.append("Scheduler dispatch request_id mismatch")
    if reply.get("request_id") != route.get("request_id"):
        issues.append("Scheduler route reply request_id mismatch")
    if reply.get("route_id") != route.get("route_id"):
        issues.append("Scheduler route reply route_id mismatch")
    if reply.get("task_id") != route.get("task_id"):
        issues.append("Scheduler route reply task_id mismatch")
    if reply.get("status") != "ready":
        issues.append("Scheduler route reply must be ready")

    request = _mapping(work_package.get("authoritative_request"))
    if not _text(request.get("title")):
        issues.append("authoritative request title must not be empty")
    if not _text(request.get("body")):
        issues.append("authoritative request body must not be empty")
    number = issue.get("number")
    if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
        issues.append("source issue number must be a positive integer")
    generation = work_package.get("context_generation")
    if (
        isinstance(generation, bool)
        or not isinstance(generation, int)
        or generation < 0
    ):
        issues.append("context_generation must be a non-negative integer")
    return issues


def _evidence_refs(*, suffix: str, advisory_present: bool) -> tuple[str, ...]:
    refs = [f"artifact:github-request-{suffix}"]
    if advisory_present:
        refs.append(f"artifact:github-advisory-{suffix}")
    return tuple(refs)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _require_text(name: str, value: object) -> str:
    text = _text(value)
    if not text:
        raise GitHubResearchLoveFirstVisitDispatchError(
            f"{name} must not be empty"
        )
    return text


def _invalid(
    status: str,
    issues: tuple[str, ...] | list[str],
    *,
    surface: GitHubResearchLoveFirstVisitSurface | None = None,
    handler_action: str = "",
    scheduler_receipt: Mapping[str, Any] | None = None,
) -> GitHubResearchLoveFirstVisitDispatchResult:
    return GitHubResearchLoveFirstVisitDispatchResult(
        valid=False,
        status=status,
        issues=tuple(dict.fromkeys(str(item) for item in issues if str(item))),
        handler_action=handler_action,
        surface=surface,
        scheduler_receipt=dict(scheduler_receipt or {}),
    )


__all__ = (
    "GitHubResearchLoveFirstVisitDispatchCommand",
    "GitHubResearchLoveFirstVisitDispatchError",
    "GitHubResearchLoveFirstVisitDispatchResult",
    "GitHubResearchLoveFirstVisitSurface",
    "GitHubResearchLoveRuntimeResolver",
    "SCHEMA",
    "build_first_love_visit_surface_from_github_research",
    "dispatch_first_love_visit_from_github_research",
)
