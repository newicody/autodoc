"""Second real love specialist and authorized two-visit collaboration for r11.

The r10 provider remains unchanged as an historical proof that only the first
specialist was active.  This module adds a collaborative provider that delegates
first-specialist visits to r10 and executes the second specialist only when an
exact digest-backed first-analysis artifact is supplied in a Scheduler-approved
second task.

No Scheduler, queue, EventBus, SQL/Qdrant authority, ControlProxy, model pool or
GitHub client is created here.  The module prepares continuation messages and a
second visit, but execution still requires a new submission to the existing
Scheduler.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable
import unicodedata

from context.deterministic_fake_laboratory_provider_0273 import (
    LaboratoryProvider,
    LaboratoryProviderExecutionError,
)
from context.laboratory_framework_contract_0273 import (
    LABORATORY_REGISTRY_BINDING_SCHEMA,
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LABORATORY_VISIT_RESULT_SCHEMA,
    LaboratoryContractError,
    LaboratoryDescriptor,
    LaboratoryRegistryBindingPlan,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
    LaboratoryVisitResult,
    validate_laboratory_visit_result,
)
from context.love_study_contracts_0287 import (
    LOVE_ANALYSIS_FINDING_SCHEMA,
    LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
    LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF,
    LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA,
    LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
    LOVE_STUDY_REQUEST_CONTRACT_REF,
    SPECIALIST_TASK_RESULT_CONTRACT_REF,
    LoveAnalysisFinding,
    LoveConceptAffectAnalysis,
    LoveRelationalDynamicsAnalysis,
    LoveStudyRequest,
)
from context.native_love_laboratory_first_specialist_0287 import (
    NATIVE_LOVE_LABORATORY_COMPONENT_ID,
    NATIVE_LOVE_LABORATORY_SOURCE_PATHS,
    LoveLaboratoryInputResolver,
    NativeLoveLaboratoryProvider,
    build_native_love_laboratory_descriptor,
    build_native_love_laboratory_provider,
)
from context.scheduler_owned_runtime_registry_0257 import (
    SchedulerOwnedRuntimeComponentRegistration,
    SchedulerOwnedRuntimeRegistry,
    validate_scheduler_owned_runtime_registry,
)
from context.specialist_laboratory_message_v2_0287 import (
    SPECIALIST_ARTIFACT_REFERENCE_SCHEMA,
    SPECIALIST_LABORATORY_CONVERSATION_V2_SCHEMA,
    SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA,
    SpecialistArtifactReference,
    SpecialistLaboratoryConversationV2,
    SpecialistLaboratoryMessageV2,
    build_completion_message_v2,
    compute_payload_sha256,
    stable_idempotency_key,
)
from context.specialist_multitask_model_0287 import (
    SPECIALIST_TASK_REQUEST_SCHEMA,
    SPECIALIST_TASK_RESULT_SCHEMA,
    SpecialistTaskRequest,
    SpecialistTaskResult,
)

NATIVE_LOVE_COLLABORATION_VERSION = "0287.r7.r11"
NATIVE_LOVE_COLLABORATIVE_PROVIDER_SCHEMA = (
    "missipy.laboratory.provider.love_native_collaborative.v1"
)
NATIVE_LOVE_COLLABORATIVE_EXECUTION_SCHEMA = (
    "missipy.laboratory.execution.love_native_collaborative.v1"
)
NATIVE_LOVE_COLLABORATION_PREPARATION_SCHEMA = (
    "missipy.love.collaboration_preparation.v1"
)
NATIVE_LOVE_COLLABORATION_RECORD_SCHEMA = (
    "missipy.love.collaboration_record.v1"
)
NATIVE_LOVE_COLLABORATIVE_COMPONENT_ID = NATIVE_LOVE_LABORATORY_COMPONENT_ID
NATIVE_LOVE_COLLABORATIVE_SOURCE_PATHS = tuple(
    dict.fromkeys(
        NATIVE_LOVE_LABORATORY_SOURCE_PATHS
        + (
            "src/context/native_love_laboratory_second_specialist_0287.py",
            "src/context/"
            "native_love_laboratory_collaboration_scheduler_binding_0287.py",
        )
    )
)

_SECOND_ANALYSIS_CAPABILITIES = frozenset(
    {
        "love.relational_dynamics",
        "love.reciprocity_analysis",
        "love.communication_analysis",
        "recommendation.build",
    }
)
_SECOND_GENERIC_CAPABILITIES = frozenset(
    {
        "analysis.critique",
        "analysis.validate",
    }
)
_IMPLEMENTED_SECOND_CAPABILITIES = (
    _SECOND_ANALYSIS_CAPABILITIES | _SECOND_GENERIC_CAPABILITIES
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|[\n;]+")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_RELATIONAL_LEXICON: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "reciprocity": (
            "reciproque",
            "reciprocite",
            "mutuel",
            "mutuelle",
            "tous les deux",
            "ensemble",
        ),
        "communication": (
            "parler",
            "discussion",
            "discuter",
            "dire",
            "exprimer",
            "conversation",
            "dialogue",
        ),
        "commitment": (
            "engagement",
            "engage",
            "avenir",
            "projet",
            "exclusif",
            "relation serieuse",
        ),
        "boundaries": (
            "limite",
            "respect",
            "espace",
            "besoin",
            "consentement",
            "pression",
        ),
        "asymmetry": (
            "toujours moi",
            "seul",
            "seule",
            "jamais lui",
            "jamais elle",
            "plus que",
            "moins que",
            "sens unique",
        ),
        "conflict": (
            "conflit",
            "dispute",
            "colere",
            "silence",
            "reproche",
            "tension",
        ),
        "distance": (
            "distance",
            "eloigne",
            "eloignement",
            "separation",
            "absent",
            "absence",
        ),
        "trust": (
            "confiance",
            "honnete",
            "honnetete",
            "securite",
            "trahison",
        ),
    }
)


class NativeLoveCollaborationError(RuntimeError):
    """Raised when the authorized two-specialist chain is incoherent."""


@runtime_checkable
class CollaborativeLoveLaboratoryInputResolver(
    LoveLaboratoryInputResolver,
    Protocol,
):
    """Resolve studies, tasks and authorized first-analysis artifacts."""

    def resolve_concept_analysis(
        self,
        request: LaboratoryVisitRequest,
        artifact: SpecialistArtifactReference,
    ) -> LoveConceptAffectAnalysis:
        """Return the analysis that exactly matches one authorized artifact."""


@dataclass
class InMemoryCollaborativeLoveLaboratoryInputResolver:
    """Mutable runtime resolver used by local collaboration and tests.

    The resolver is not durable authority.  It models the injected runtime view
    that a future SQL-backed resolver will expose through the same protocol.
    Registration is append-only and collision checked.
    """

    studies: Mapping[str, LoveStudyRequest]
    tasks: Mapping[str, SpecialistTaskRequest]
    concept_analyses: Mapping[str, LoveConceptAffectAnalysis] = field(
        default_factory=dict
    )
    concept_artifacts: Mapping[str, SpecialistArtifactReference] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self._studies = dict(self.studies)
        self._tasks = dict(self.tasks)
        self._concept_analyses = dict(self.concept_analyses)
        self._concept_artifacts = dict(self.concept_artifacts)
        if not self._studies or not self._tasks:
            raise NativeLoveCollaborationError(
                "resolver requires at least one study and one task"
            )
        if not all(
            isinstance(item, LoveStudyRequest)
            for item in self._studies.values()
        ):
            raise NativeLoveCollaborationError(
                "studies must contain LoveStudyRequest values"
            )
        if not all(
            isinstance(item, SpecialistTaskRequest)
            for item in self._tasks.values()
        ):
            raise NativeLoveCollaborationError(
                "tasks must contain SpecialistTaskRequest values"
            )
        for artifact_ref, analysis in self._concept_analyses.items():
            artifact = self._concept_artifacts.get(artifact_ref)
            if artifact is None:
                raise NativeLoveCollaborationError(
                    "each concept analysis requires its artifact reference"
                )
            _validate_analysis_artifact(analysis, artifact)

    def resolve_study(self, request: LaboratoryVisitRequest) -> LoveStudyRequest:
        try:
            return self._studies[request.source_candidate_ref]
        except KeyError as exc:
            raise NativeLoveCollaborationError(
                "source_candidate_ref does not resolve to a love study"
            ) from exc

    def resolve_task(
        self,
        request: LaboratoryVisitRequest,
    ) -> SpecialistTaskRequest:
        try:
            return self._tasks[request.objective_ref]
        except KeyError as exc:
            raise NativeLoveCollaborationError(
                "objective_ref does not resolve to a specialist task"
            ) from exc

    def register_task(self, task: SpecialistTaskRequest) -> None:
        """Register a Scheduler-approved task idempotently."""

        if not isinstance(task, SpecialistTaskRequest):
            raise TypeError("task must be SpecialistTaskRequest")
        existing = self._tasks.get(task.task_ref)
        if existing is not None and existing != task:
            raise NativeLoveCollaborationError(
                "task_ref collision in collaboration resolver"
            )
        self._tasks[task.task_ref] = task

    def register_concept_analysis(
        self,
        analysis: LoveConceptAffectAnalysis,
        artifact: SpecialistArtifactReference,
    ) -> None:
        """Register one exact first-analysis artifact idempotently."""

        _validate_analysis_artifact(analysis, artifact)
        existing_analysis = self._concept_analyses.get(artifact.artifact_ref)
        existing_artifact = self._concept_artifacts.get(artifact.artifact_ref)
        if existing_analysis is not None and existing_analysis != analysis:
            raise NativeLoveCollaborationError(
                "concept analysis artifact collision"
            )
        if existing_artifact is not None and existing_artifact != artifact:
            raise NativeLoveCollaborationError(
                "concept artifact metadata collision"
            )
        self._concept_analyses[artifact.artifact_ref] = analysis
        self._concept_artifacts[artifact.artifact_ref] = artifact

    def resolve_concept_analysis(
        self,
        request: LaboratoryVisitRequest,
        artifact: SpecialistArtifactReference,
    ) -> LoveConceptAffectAnalysis:
        try:
            stored_artifact = self._concept_artifacts[artifact.artifact_ref]
            analysis = self._concept_analyses[artifact.artifact_ref]
        except KeyError as exc:
            raise NativeLoveCollaborationError(
                "authorized first-analysis artifact is unavailable"
            ) from exc
        if stored_artifact != artifact:
            raise NativeLoveCollaborationError(
                "first-analysis artifact metadata differs from registered value"
            )
        _validate_analysis_artifact(analysis, artifact)
        if analysis.study_ref != self.resolve_study(request).study_ref:
            raise NativeLoveCollaborationError(
                "first analysis belongs to another study"
            )
        return analysis


@dataclass(frozen=True, slots=True)
class NativeLoveCollaborativeExecutionRecord:
    """Proof that one visit executed through the collaborative provider."""

    schema: str
    provider_ref: str
    request: LaboratoryVisitRequest
    task: SpecialistTaskRequest
    study_ref: str
    result: LaboratoryVisitResult
    specialist_stage: str
    result_valid: bool
    validation_issues: tuple[str, ...] = ()
    real_specialist_executed: bool = True
    content_dependent_result: bool = True
    scheduler_path_required: bool = True
    direct_followup_execution: bool = False
    global_synthesis_created: bool = False
    durable_write_performed: bool = False
    github_mutation_performed: bool = False

    def __post_init__(self) -> None:
        if self.schema != NATIVE_LOVE_COLLABORATIVE_EXECUTION_SCHEMA:
            raise NativeLoveCollaborationError(
                "unsupported collaborative execution schema"
            )
        if self.provider_ref != LOVE_STUDIES_LABORATORY_REF:
            raise NativeLoveCollaborationError("unexpected provider_ref")
        if self.task.task_ref != self.request.objective_ref:
            raise NativeLoveCollaborationError("task and visit mismatch")
        if self.result.visit_ref != self.request.visit_ref:
            raise NativeLoveCollaborationError("result and visit mismatch")
        if self.specialist_stage not in {"first_analysis", "second_analysis"}:
            raise NativeLoveCollaborationError("unsupported specialist stage")
        if self.result_valid != (not self.validation_issues):
            raise NativeLoveCollaborationError(
                "result_valid must reflect validation issues"
            )
        if not self.real_specialist_executed:
            raise NativeLoveCollaborationError("specialist execution is required")
        if not self.content_dependent_result:
            raise NativeLoveCollaborationError(
                "collaborative result must depend on content"
            )
        if not self.scheduler_path_required:
            raise NativeLoveCollaborationError("Scheduler path is mandatory")
        if any(
            (
                self.direct_followup_execution,
                self.global_synthesis_created,
                self.durable_write_performed,
                self.github_mutation_performed,
            )
        ):
            raise NativeLoveCollaborationError(
                "r11 execution must preserve bounded ownership"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "provider_ref": self.provider_ref,
            "request": self.request.to_mapping(),
            "task": self.task.to_mapping(),
            "study_ref": self.study_ref,
            "result": self.result.to_mapping(),
            "specialist_stage": self.specialist_stage,
            "result_valid": self.result_valid,
            "validation_issues": list(self.validation_issues),
            "real_specialist_executed": self.real_specialist_executed,
            "content_dependent_result": self.content_dependent_result,
            "scheduler_path_required": self.scheduler_path_required,
            "direct_followup_execution": self.direct_followup_execution,
            "global_synthesis_created": self.global_synthesis_created,
            "durable_write_performed": self.durable_write_performed,
            "github_mutation_performed": self.github_mutation_performed,
        }


@dataclass(frozen=True, slots=True)
class NativeLoveCollaborativeLaboratoryProvider:
    """Provider executing both specialists without owning their sequence."""

    descriptor: LaboratoryDescriptor
    resolver: CollaborativeLoveLaboratoryInputResolver
    first_provider: NativeLoveLaboratoryProvider
    provider_schema: str = NATIVE_LOVE_COLLABORATIVE_PROVIDER_SCHEMA

    def __post_init__(self) -> None:
        if self.provider_schema != NATIVE_LOVE_COLLABORATIVE_PROVIDER_SCHEMA:
            raise NativeLoveCollaborationError(
                "unsupported collaborative provider schema"
            )
        if not isinstance(self, LaboratoryProvider):
            raise NativeLoveCollaborationError(
                "provider must implement LaboratoryProvider"
            )
        if self.descriptor.laboratory_ref != LOVE_STUDIES_LABORATORY_REF:
            raise NativeLoveCollaborationError("unexpected laboratory_ref")
        if self.descriptor.provider_kind != "autodoc_native":
            raise NativeLoveCollaborationError(
                "collaborative provider must be autodoc_native"
            )
        if self.descriptor.execution_boundary != "in_process":
            raise NativeLoveCollaborationError(
                "collaborative provider must execute in_process"
            )
        if self.descriptor.availability != "ready" or not self.descriptor.enabled:
            raise NativeLoveCollaborationError("provider descriptor must be ready")
        if self.descriptor.network_allowed:
            raise NativeLoveCollaborationError("network access must remain disabled")
        if not isinstance(self.resolver, CollaborativeLoveLaboratoryInputResolver):
            raise NativeLoveCollaborationError(
                "resolver must implement collaborative input protocol"
            )
        if self.first_provider.resolver is not self.resolver:
            raise NativeLoveCollaborationError(
                "first provider and collaborative provider must share resolver"
            )

    def execute(self, request: LaboratoryVisitRequest) -> LaboratoryVisitResult:
        if request.specialist_ref == LOVE_CONCEPT_AFFECT_SPECIALIST_REF:
            return self.first_provider.execute(request)
        if request.specialist_ref != LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF:
            raise NativeLoveCollaborationError(
                "collaborative provider supports only declared love specialists"
            )
        _validate_second_visit_surface(self.descriptor, request)
        study = self.resolver.resolve_study(request)
        task = self.resolver.resolve_task(request)
        source_artifact = _resolve_task_source_artifact(task)
        source_analysis = self.resolver.resolve_concept_analysis(
            request,
            source_artifact,
        )
        _validate_second_inputs(
            request=request,
            study=study,
            task=task,
            source_analysis=source_analysis,
            source_artifact=source_artifact,
        )
        result = _execute_second_specialist(
            request=request,
            study=study,
            task=task,
            source_analysis=source_analysis,
            source_artifact=source_artifact,
        )
        issues = validate_laboratory_visit_result(request, result)
        if issues:
            raise LaboratoryProviderExecutionError("; ".join(issues))
        return result


def build_native_love_collaborative_descriptor() -> LaboratoryDescriptor:
    """Promote the r10 descriptor to a two-specialist r11 runtime."""

    descriptor = build_native_love_laboratory_descriptor()
    return replace(
        descriptor,
        metadata=(
            ("runtime_phase", "0287-r7-r11"),
            ("scheduler_owned_registry", "true"),
            ("first_specialist_backend", "stdlib_lexical_v1"),
            ("second_specialist_backend", "stdlib_relational_v1"),
            ("first_specialist_real", "true"),
            ("second_specialist_real", "true"),
            ("message_contract", "specialist_laboratory_message_v2"),
            ("direct_followup_execution", "false"),
            ("global_synthesis", "later_liaison_step"),
        ),
    )


def build_native_love_collaborative_binding_plan(
) -> LaboratoryRegistryBindingPlan:
    """Upgrade the existing laboratory registration without adding a second one."""

    descriptor = build_native_love_collaborative_descriptor()
    return LaboratoryRegistryBindingPlan(
        schema=LABORATORY_REGISTRY_BINDING_SCHEMA,
        laboratory_ref=descriptor.laboratory_ref,
        component_id=NATIVE_LOVE_COLLABORATIVE_COMPONENT_ID,
        capabilities=descriptor.capabilities,
        provider_source_paths=NATIVE_LOVE_COLLABORATIVE_SOURCE_PATHS,
        ready_for_registry_attachment=True,
        provider_active=True,
    )


def build_native_love_collaborative_registration(
) -> SchedulerOwnedRuntimeComponentRegistration:
    """Build the r11 revision of the existing Scheduler-owned registration."""

    plan = build_native_love_collaborative_binding_plan()
    return SchedulerOwnedRuntimeComponentRegistration(
        component_id=plan.component_id,
        surface="laboratory_provider",
        owner=plan.owner,
        role=plan.role,
        capabilities=plan.capabilities,
        depends_on=(),
        source_paths=plan.provider_source_paths,
        runtime_api_kind="scheduler_owned_object",
        selected_from_existing_surfaces=False,
    )


def upgrade_native_love_collaborative_registration(
    registry: SchedulerOwnedRuntimeRegistry,
) -> SchedulerOwnedRuntimeRegistry:
    """Replace the r10 registration in place, or append it if still absent."""

    registration = build_native_love_collaborative_registration()
    found = False
    registrations: list[SchedulerOwnedRuntimeComponentRegistration] = []
    for item in registry.registrations:
        if item.component_id != registration.component_id:
            registrations.append(item)
            continue
        found = True
        registrations.append(registration)
    if not found:
        registrations.append(registration)
    updated = SchedulerOwnedRuntimeRegistry(
        registrations=tuple(registrations),
        source_map_complete=registry.source_map_complete,
        owner=registry.owner,
        launcher_bootstrap_only=registry.launcher_bootstrap_only,
        eventbus_observation_only=registry.eventbus_observation_only,
        no_cli_per_component=registry.no_cli_per_component,
        creates_runtime_manager=registry.creates_runtime_manager,
        instantiates_components=registry.instantiates_components,
    )
    issues = validate_scheduler_owned_runtime_registry(updated)
    if issues:
        raise LaboratoryContractError("; ".join(issues))
    matching = tuple(
        item
        for item in updated.registrations
        if item.component_id == registration.component_id
    )
    if matching != (registration,):
        raise LaboratoryContractError(
            "native love laboratory must have one Scheduler-owned registration"
        )
    return updated


def build_native_love_collaborative_provider(
    resolver: CollaborativeLoveLaboratoryInputResolver,
) -> NativeLoveCollaborativeLaboratoryProvider:
    """Build one provider reusing the exact r10 first-specialist provider."""

    first_provider = build_native_love_laboratory_provider(resolver)
    return NativeLoveCollaborativeLaboratoryProvider(
        descriptor=build_native_love_collaborative_descriptor(),
        resolver=resolver,
        first_provider=first_provider,
    )


def execute_native_love_collaborative_visit(
    request: LaboratoryVisitRequest,
    *,
    provider: NativeLoveCollaborativeLaboratoryProvider,
) -> NativeLoveCollaborativeExecutionRecord:
    """Execute one already-authorized visit through the r11 provider."""

    if not isinstance(provider, NativeLoveCollaborativeLaboratoryProvider):
        raise TypeError(
            "provider must be NativeLoveCollaborativeLaboratoryProvider"
        )
    result = provider.execute(request)
    task = provider.resolver.resolve_task(request)
    study = provider.resolver.resolve_study(request)
    issues = validate_laboratory_visit_result(request, result)
    stage = (
        "first_analysis"
        if request.specialist_ref == LOVE_CONCEPT_AFFECT_SPECIALIST_REF
        else "second_analysis"
    )
    return NativeLoveCollaborativeExecutionRecord(
        schema=NATIVE_LOVE_COLLABORATIVE_EXECUTION_SCHEMA,
        provider_ref=provider.descriptor.laboratory_ref,
        request=request,
        task=task,
        study_ref=study.study_ref,
        result=result,
        specialist_stage=stage,
        result_valid=not issues,
        validation_issues=issues,
    )


def concept_analysis_from_visit_result(
    result: LaboratoryVisitResult,
) -> LoveConceptAffectAnalysis:
    """Rebuild the public first-analysis contract from a visit result."""

    if result.output_contract_ref != LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF:
        raise NativeLoveCollaborationError(
            "visit result does not contain a concept-affect analysis"
        )
    payload = dict(result.machine_result)
    if payload.get("schema") != LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA:
        raise NativeLoveCollaborationError(
            "first analysis payload has an unsupported schema"
        )
    findings_raw = payload.get("findings")
    if not isinstance(findings_raw, (list, tuple)):
        raise NativeLoveCollaborationError("first analysis findings are invalid")
    findings = tuple(_finding_from_mapping(item) for item in findings_raw)
    return LoveConceptAffectAnalysis(
        schema=str(payload["schema"]),
        analysis_ref=str(payload["analysis_ref"]),
        study_ref=str(payload["study_ref"]),
        specialist_ref=str(payload["specialist_ref"]),
        context_revision_ref=str(payload["context_revision_ref"]),
        findings=findings,
        concepts=_string_tuple(payload.get("concepts"), "concepts"),
        affects=_string_tuple(payload.get("affects"), "affects"),
        uncertainties=_string_tuple(
            payload.get("uncertainties"),
            "uncertainties",
        ),
        contradictions=_string_tuple(
            payload.get("contradictions"),
            "contradictions",
        ),
        limitations=_string_tuple(payload.get("limitations"), "limitations"),
        recommendations=_string_tuple(
            payload.get("recommendations"),
            "recommendations",
        ),
        evidence_refs=_string_tuple(
            payload.get("evidence_refs"),
            "evidence_refs",
        ),
        artifact_refs=_string_tuple(
            payload.get("artifact_refs"),
            "artifact_refs",
        ),
        local_synthesis=_optional_text(payload.get("local_synthesis")),
        contribution_kind=str(payload.get("contribution_kind", "domain_analysis")),
    )


def build_concept_analysis_artifact(
    analysis: LoveConceptAffectAnalysis,
    *,
    producer_visit_ref: str,
) -> SpecialistArtifactReference:
    """Build the canonical digest-backed reference for the first analysis."""

    return _artifact_reference_for_analysis(
        analysis=analysis,
        producer_visit_ref=producer_visit_ref,
        producer_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    )


def build_relational_analysis_artifact(
    analysis: LoveRelationalDynamicsAnalysis,
    *,
    producer_visit_ref: str,
) -> SpecialistArtifactReference:
    """Build the canonical digest-backed reference for the second analysis."""

    return _artifact_reference_for_analysis(
        analysis=analysis,
        producer_visit_ref=producer_visit_ref,
        producer_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
    )


@dataclass(frozen=True, slots=True)
class NativeLoveCollaborationPreparation:
    """Prepared second task, visit and v2 continuation without execution."""

    schema: str
    first_analysis: LoveConceptAffectAnalysis
    first_artifact: SpecialistArtifactReference
    first_demand: SpecialistLaboratoryMessageV2
    first_completion: SpecialistLaboratoryMessageV2
    second_task: SpecialistTaskRequest
    second_visit: LaboratoryVisitRequest
    second_demand: SpecialistLaboratoryMessageV2
    scheduler_submission_required: bool = True
    task_created_by_scheduler: bool = False
    second_visit_executed: bool = False
    direct_specialist_invocation: bool = False

    def __post_init__(self) -> None:
        if self.schema != NATIVE_LOVE_COLLABORATION_PREPARATION_SCHEMA:
            raise NativeLoveCollaborationError(
                "unsupported collaboration preparation schema"
            )
        if self.first_analysis.analysis_ref not in _source_refs(self.second_task):
            raise NativeLoveCollaborationError(
                "second task must reference the first analysis"
            )
        if self.first_artifact not in self.second_task.input_artifact_refs:
            raise NativeLoveCollaborationError(
                "second task must carry the first-analysis artifact"
            )
        if self.second_visit.objective_ref != self.second_task.task_ref:
            raise NativeLoveCollaborationError("second task and visit mismatch")
        if self.second_visit.parent_visit_ref != self.first_completion.visit_ref:
            raise NativeLoveCollaborationError(
                "second visit must continue the first visit"
            )
        if self.second_demand.continuation_of_message_ref != (
            self.first_completion.message_ref
        ):
            raise NativeLoveCollaborationError(
                "second demand must continue the first completion"
            )
        forbidden = (
            not self.scheduler_submission_required,
            self.task_created_by_scheduler,
            self.second_visit_executed,
            self.direct_specialist_invocation,
        )
        if any(forbidden):
            raise NativeLoveCollaborationError(
                "preparation must not execute or authorize the second visit"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "first_analysis": self.first_analysis.to_mapping(),
            "first_artifact": self.first_artifact.to_mapping(),
            "first_demand": self.first_demand.to_mapping(),
            "first_completion": self.first_completion.to_mapping(),
            "second_task": self.second_task.to_mapping(),
            "second_visit": self.second_visit.to_mapping(),
            "second_demand": self.second_demand.to_mapping(),
            "scheduler_submission_required": self.scheduler_submission_required,
            "task_created_by_scheduler": self.task_created_by_scheduler,
            "second_visit_executed": self.second_visit_executed,
            "direct_specialist_invocation": self.direct_specialist_invocation,
        }


def prepare_second_specialist_collaboration(
    *,
    first_visit: LaboratoryVisitRequest,
    first_result: LaboratoryVisitResult,
    second_task_ref: str,
    second_visit_ref: str,
    capability: str = "love.relational_dynamics",
    objective: str = "Analyser les dynamiques relationnelles et les tensions.",
) -> NativeLoveCollaborationPreparation:
    """Prepare the continuation that must be submitted to the Scheduler."""

    if first_visit.specialist_ref != LOVE_CONCEPT_AFFECT_SPECIALIST_REF:
        raise NativeLoveCollaborationError(
            "first visit must target the concept-affect specialist"
        )
    if first_result.visit_ref != first_visit.visit_ref:
        raise NativeLoveCollaborationError("first visit and result mismatch")
    if capability not in _IMPLEMENTED_SECOND_CAPABILITIES:
        raise NativeLoveCollaborationError(
            "unsupported second-specialist capability"
        )
    if first_visit.conversation_ref is None:
        raise NativeLoveCollaborationError(
            "first visit requires a conversation_ref"
        )
    first_analysis = concept_analysis_from_visit_result(first_result)
    first_artifact = build_concept_analysis_artifact(
        first_analysis,
        producer_visit_ref=first_visit.visit_ref,
    )
    first_demand = _build_first_demand(first_visit)
    first_completion = build_completion_message_v2(
        demand_message=first_demand,
        message_ref=_message_ref(first_visit.visit_ref, "completion"),
        sequence_no=1,
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        visit_ref=first_visit.visit_ref,
        human_representation=first_result.human_representation,
        artifact_refs=(first_artifact,),
        payload={
            "status": "completed",
            "analysis_ref": first_analysis.analysis_ref,
            "artifact_ref": first_artifact.artifact_ref,
        },
    )
    output_contract = (
        SPECIALIST_TASK_RESULT_CONTRACT_REF
        if capability in _SECOND_GENERIC_CAPABILITIES
        else LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF
    )
    input_contract = (
        LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF
        if capability in _SECOND_GENERIC_CAPABILITIES
        else LOVE_STUDY_REQUEST_CONTRACT_REF
    )
    task = SpecialistTaskRequest(
        schema=SPECIALIST_TASK_REQUEST_SCHEMA,
        task_ref=second_task_ref,
        plan_ref=_second_plan_ref(first_visit.visit_ref),
        mission_ref=_second_mission_ref(first_visit.visit_ref),
        specialist_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        task_type_ref=f"task-type:{capability}",
        capability=capability,
        objective=objective,
        input_contract_ref=input_contract,
        expected_output_contract_ref=output_contract,
        conversation_ref=first_visit.conversation_ref,
        return_route_ref=first_visit.return_route_ref,
        constraints=(
            "Ne pas inférer les intentions d'une personne absente.",
            "Conserver la provenance de la première analyse.",
        ),
        success_criteria=(
            "Produire une analyse relationnelle distincte de la première.",
            "Référencer explicitement l'analyse source et ses preuves.",
        ),
        context_refs=first_visit.context_refs,
        evidence_refs=tuple(
            dict.fromkeys(first_visit.evidence_refs + first_analysis.evidence_refs)
        ),
        input_artifact_refs=(first_artifact,),
        priority=100,
        idempotency_key=stable_idempotency_key(
            first_visit.visit_ref,
            second_task_ref,
            capability,
        ),
        metadata={
            "source_analysis_ref": first_analysis.analysis_ref,
            "source_artifact_ref": first_artifact.artifact_ref,
            "context_revision_ref": first_analysis.context_revision_ref,
            "scheduler_submission_required": True,
            "global_synthesis_requested": False,
        },
    )
    visit = LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref=second_visit_ref,
        laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        specialist_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        objective_ref=task.task_ref,
        source_candidate_ref=first_visit.source_candidate_ref,
        context_generation=first_visit.context_generation,
        input_contract_ref=task.input_contract_ref,
        expected_output_contract_ref=task.expected_output_contract_ref,
        resource_budget=LaboratoryResourceBudget(
            max_duration_ms=first_visit.resource_budget.max_duration_ms,
            max_output_chars=first_visit.resource_budget.max_output_chars,
            max_context_refs=first_visit.resource_budget.max_context_refs,
            max_evidence_refs=first_visit.resource_budget.max_evidence_refs,
            max_followup_requests=first_visit.resource_budget.max_followup_requests,
            max_specialist_messages=first_visit.resource_budget.max_specialist_messages,
            max_external_calls=0,
            allow_network=False,
        ),
        return_route_ref=first_visit.return_route_ref,
        context_refs=task.context_refs,
        evidence_refs=task.evidence_refs,
        origin_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        target_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        conversation_ref=first_visit.conversation_ref,
        parent_visit_ref=first_visit.visit_ref,
        metadata=(
            ("phase", "0287-r7-r11"),
            ("source_analysis_ref", first_analysis.analysis_ref),
            ("source_artifact_ref", first_artifact.artifact_ref),
            ("scheduler_submission_required", "true"),
        ),
    )
    second_demand = _build_second_demand(
        visit=visit,
        task=task,
        first_completion=first_completion,
        first_artifact=first_artifact,
    )
    return NativeLoveCollaborationPreparation(
        schema=NATIVE_LOVE_COLLABORATION_PREPARATION_SCHEMA,
        first_analysis=first_analysis,
        first_artifact=first_artifact,
        first_demand=first_demand,
        first_completion=first_completion,
        second_task=task,
        second_visit=visit,
        second_demand=second_demand,
    )


@dataclass(frozen=True, slots=True)
class NativeLoveCollaborationRecord:
    """Final r11 proof after two separately scheduled visits."""

    schema: str
    first_execution: NativeLoveCollaborativeExecutionRecord
    second_execution: NativeLoveCollaborativeExecutionRecord
    conversation: SpecialistLaboratoryConversationV2
    second_analysis: LoveRelationalDynamicsAnalysis
    second_artifact: SpecialistArtifactReference
    scheduler_receipt_refs: tuple[str, str]
    same_scheduler_required: bool = True
    direct_specialist_invocation: bool = False
    global_synthesis_created: bool = False

    def __post_init__(self) -> None:
        if self.schema != NATIVE_LOVE_COLLABORATION_RECORD_SCHEMA:
            raise NativeLoveCollaborationError(
                "unsupported collaboration record schema"
            )
        if self.first_execution.specialist_stage != "first_analysis":
            raise NativeLoveCollaborationError("first execution stage mismatch")
        if self.second_execution.specialist_stage != "second_analysis":
            raise NativeLoveCollaborationError("second execution stage mismatch")
        if self.second_analysis.source_analysis_refs != (
            concept_analysis_from_visit_result(
                self.first_execution.result
            ).analysis_ref,
        ):
            raise NativeLoveCollaborationError(
                "second analysis must consume the first analysis"
            )
        if not self.conversation.closed or len(self.conversation.messages) != 4:
            raise NativeLoveCollaborationError(
                "collaboration conversation must close with four messages"
            )
        if len(set(self.scheduler_receipt_refs)) != 2:
            raise NativeLoveCollaborationError(
                "two distinct Scheduler receipts are required"
            )
        if not self.same_scheduler_required:
            raise NativeLoveCollaborationError(
                "the same Scheduler authority must own both visits"
            )
        if self.direct_specialist_invocation or self.global_synthesis_created:
            raise NativeLoveCollaborationError(
                "collaboration must not bypass Scheduler or synthesize globally"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "first_execution": self.first_execution.to_mapping(),
            "second_execution": self.second_execution.to_mapping(),
            "conversation": self.conversation.to_mapping(),
            "second_analysis": self.second_analysis.to_mapping(),
            "second_artifact": self.second_artifact.to_mapping(),
            "scheduler_receipt_refs": list(self.scheduler_receipt_refs),
            "same_scheduler_required": self.same_scheduler_required,
            "direct_specialist_invocation": self.direct_specialist_invocation,
            "global_synthesis_created": self.global_synthesis_created,
        }


def build_completed_collaboration_record(
    *,
    preparation: NativeLoveCollaborationPreparation,
    first_execution: NativeLoveCollaborativeExecutionRecord,
    second_execution: NativeLoveCollaborativeExecutionRecord,
    first_scheduler_receipt_ref: str,
    second_scheduler_receipt_ref: str,
) -> NativeLoveCollaborationRecord:
    """Close messages after the Scheduler returned the second visit."""

    second_analysis = relational_analysis_from_visit_result(
        second_execution.result
    )
    second_artifact = build_relational_analysis_artifact(
        second_analysis,
        producer_visit_ref=second_execution.request.visit_ref,
    )
    second_completion = build_completion_message_v2(
        demand_message=preparation.second_demand,
        message_ref=_message_ref(
            second_execution.request.visit_ref,
            "completion",
        ),
        sequence_no=3,
        specialist_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        visit_ref=second_execution.request.visit_ref,
        human_representation=second_execution.result.human_representation,
        artifact_refs=(second_artifact,),
        payload={
            "status": "completed",
            "analysis_ref": second_analysis.analysis_ref,
            "artifact_ref": second_artifact.artifact_ref,
            "source_analysis_refs": list(second_analysis.source_analysis_refs),
        },
    )
    conversation = SpecialistLaboratoryConversationV2(
        schema=SPECIALIST_LABORATORY_CONVERSATION_V2_SCHEMA,
        conversation_ref=preparation.first_demand.conversation_ref,
        correlation_ref=preparation.first_demand.correlation_ref,
        return_route_ref=preparation.first_demand.return_route_ref,
        messages=(
            preparation.first_demand,
            preparation.first_completion,
            preparation.second_demand,
            second_completion,
        ),
        closed=True,
    )
    return NativeLoveCollaborationRecord(
        schema=NATIVE_LOVE_COLLABORATION_RECORD_SCHEMA,
        first_execution=first_execution,
        second_execution=second_execution,
        conversation=conversation,
        second_analysis=second_analysis,
        second_artifact=second_artifact,
        scheduler_receipt_refs=(
            first_scheduler_receipt_ref,
            second_scheduler_receipt_ref,
        ),
    )


def relational_analysis_from_visit_result(
    result: LaboratoryVisitResult,
) -> LoveRelationalDynamicsAnalysis:
    """Rebuild the public second-analysis contract from a visit result."""

    if result.output_contract_ref != LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF:
        raise NativeLoveCollaborationError(
            "visit result does not contain a relational analysis"
        )
    payload = dict(result.machine_result)
    if payload.get("schema") != LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA:
        raise NativeLoveCollaborationError(
            "relational analysis payload has an unsupported schema"
        )
    findings_raw = payload.get("findings")
    if not isinstance(findings_raw, (list, tuple)):
        raise NativeLoveCollaborationError(
            "relational analysis findings are invalid"
        )
    return LoveRelationalDynamicsAnalysis(
        schema=str(payload["schema"]),
        analysis_ref=str(payload["analysis_ref"]),
        study_ref=str(payload["study_ref"]),
        specialist_ref=str(payload["specialist_ref"]),
        context_revision_ref=str(payload["context_revision_ref"]),
        findings=tuple(_finding_from_mapping(item) for item in findings_raw),
        dynamics=_string_tuple(payload.get("dynamics"), "dynamics"),
        source_analysis_refs=_string_tuple(
            payload.get("source_analysis_refs"),
            "source_analysis_refs",
        ),
        uncertainties=_string_tuple(
            payload.get("uncertainties"),
            "uncertainties",
        ),
        contradictions=_string_tuple(
            payload.get("contradictions"),
            "contradictions",
        ),
        limitations=_string_tuple(payload.get("limitations"), "limitations"),
        recommendations=_string_tuple(
            payload.get("recommendations"),
            "recommendations",
        ),
        evidence_refs=_string_tuple(
            payload.get("evidence_refs"),
            "evidence_refs",
        ),
        artifact_refs=_string_tuple(
            payload.get("artifact_refs"),
            "artifact_refs",
        ),
        local_synthesis=_optional_text(payload.get("local_synthesis")),
        contribution_kind=str(payload.get("contribution_kind", "domain_analysis")),
    )


def _validate_second_visit_surface(
    descriptor: LaboratoryDescriptor,
    request: LaboratoryVisitRequest,
) -> None:
    if request.laboratory_ref != descriptor.laboratory_ref:
        raise NativeLoveCollaborationError("request targets another laboratory")
    if request.target_laboratory_ref != descriptor.laboratory_ref:
        raise NativeLoveCollaborationError("target_laboratory_ref mismatch")
    if request.specialist_ref != LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF:
        raise NativeLoveCollaborationError("request targets another specialist")
    if request.input_contract_ref not in {
        LOVE_STUDY_REQUEST_CONTRACT_REF,
        LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
    }:
        raise NativeLoveCollaborationError("unsupported second input contract")
    if request.expected_output_contract_ref not in {
        LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF,
        SPECIALIST_TASK_RESULT_CONTRACT_REF,
    }:
        raise NativeLoveCollaborationError("unsupported second output contract")
    if request.parent_visit_ref is None:
        raise NativeLoveCollaborationError(
            "second visit must reference the first visit"
        )
    if request.conversation_ref is None:
        raise NativeLoveCollaborationError(
            "second visit requires a conversation_ref"
        )
    if request.resource_budget.allow_network:
        raise NativeLoveCollaborationError("network-enabled visits are refused")
    if request.resource_budget.max_external_calls != 0:
        raise NativeLoveCollaborationError("external calls are refused")


def _validate_second_inputs(
    *,
    request: LaboratoryVisitRequest,
    study: LoveStudyRequest,
    task: SpecialistTaskRequest,
    source_analysis: LoveConceptAffectAnalysis,
    source_artifact: SpecialistArtifactReference,
) -> None:
    if task.schema != SPECIALIST_TASK_REQUEST_SCHEMA:
        raise NativeLoveCollaborationError("unsupported task schema")
    if task.task_ref != request.objective_ref:
        raise NativeLoveCollaborationError("task_ref and objective_ref differ")
    if task.specialist_ref != LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF:
        raise NativeLoveCollaborationError("task specialist mismatch")
    if task.capability not in _IMPLEMENTED_SECOND_CAPABILITIES:
        raise NativeLoveCollaborationError("second capability is not implemented")
    if task.input_contract_ref != request.input_contract_ref:
        raise NativeLoveCollaborationError("task input contract mismatch")
    if task.expected_output_contract_ref != request.expected_output_contract_ref:
        raise NativeLoveCollaborationError("task output contract mismatch")
    if task.conversation_ref != request.conversation_ref:
        raise NativeLoveCollaborationError("task conversation mismatch")
    if task.return_route_ref != request.return_route_ref:
        raise NativeLoveCollaborationError("task return route mismatch")
    if not set(task.context_refs).issubset(request.context_refs):
        raise NativeLoveCollaborationError("task context is not authorized")
    if not set(task.evidence_refs).issubset(request.evidence_refs):
        raise NativeLoveCollaborationError("task evidence is not authorized")
    if study.study_ref != source_analysis.study_ref:
        raise NativeLoveCollaborationError("source analysis study mismatch")
    if source_analysis.analysis_ref not in _source_refs(task):
        raise NativeLoveCollaborationError(
            "task metadata does not reference source analysis"
        )
    if source_artifact not in task.input_artifact_refs:
        raise NativeLoveCollaborationError(
            "task does not carry the registered source artifact"
        )
    if task.capability in _SECOND_ANALYSIS_CAPABILITIES:
        if task.expected_output_contract_ref != (
            LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF
        ):
            raise NativeLoveCollaborationError(
                "analysis capability requires relational output"
            )
    if task.capability in _SECOND_GENERIC_CAPABILITIES:
        if task.expected_output_contract_ref != SPECIALIST_TASK_RESULT_CONTRACT_REF:
            raise NativeLoveCollaborationError(
                "critique and validation require generic task result"
            )


def _execute_second_specialist(
    *,
    request: LaboratoryVisitRequest,
    study: LoveStudyRequest,
    task: SpecialistTaskRequest,
    source_analysis: LoveConceptAffectAnalysis,
    source_artifact: SpecialistArtifactReference,
) -> LaboratoryVisitResult:
    if task.capability in _SECOND_GENERIC_CAPABILITIES:
        task_result = _build_generic_review_result(
            request=request,
            task=task,
            source_analysis=source_analysis,
            source_artifact=source_artifact,
        )
        return LaboratoryVisitResult(
            schema=LABORATORY_VISIT_RESULT_SCHEMA,
            visit_ref=request.visit_ref,
            laboratory_ref=request.laboratory_ref,
            specialist_ref=request.specialist_ref,
            status="completed",
            output_contract_ref=task.expected_output_contract_ref,
            machine_result=task_result.to_mapping(),
            human_representation=task_result.human_representation,
            confidence=0.8,
            evidence_refs=task_result.evidence_refs,
            assumptions=(
                "La validation porte sur le contrat et les preuves disponibles.",
            ),
            provenance_refs=(
                request.source_candidate_ref,
                request.objective_ref,
                source_analysis.analysis_ref,
                source_artifact.artifact_ref,
            ),
            conversation_ref=request.conversation_ref,
            parent_visit_ref=request.parent_visit_ref,
        )
    analysis = _build_relational_analysis(
        request=request,
        task=task,
        study=study,
        source_analysis=source_analysis,
    )
    return LaboratoryVisitResult(
        schema=LABORATORY_VISIT_RESULT_SCHEMA,
        visit_ref=request.visit_ref,
        laboratory_ref=request.laboratory_ref,
        specialist_ref=request.specialist_ref,
        status="completed",
        output_contract_ref=task.expected_output_contract_ref,
        machine_result=analysis.to_mapping(),
        human_representation=_render_relational_analysis(analysis),
        confidence=_analysis_confidence(analysis.findings),
        evidence_refs=analysis.evidence_refs,
        assumptions=(
            "Analyse lexicale bornée; aucune intention absente n'est inférée.",
            "La première analyse est une contribution, pas une vérité globale.",
        ),
        provenance_refs=(
            request.source_candidate_ref,
            request.objective_ref,
            source_analysis.analysis_ref,
            source_artifact.artifact_ref,
            analysis.analysis_ref,
        ),
        conversation_ref=request.conversation_ref,
        parent_visit_ref=request.parent_visit_ref,
    )


def _build_relational_analysis(
    *,
    request: LaboratoryVisitRequest,
    task: SpecialistTaskRequest,
    study: LoveStudyRequest,
    source_analysis: LoveConceptAffectAnalysis,
) -> LoveRelationalDynamicsAnalysis:
    sentences = _extract_sentences(study.subject_text)
    evidence = _build_sentence_evidence(study.study_ref, sentences)
    evidence_by_sentence = {sentence: ref for ref, sentence in evidence}
    hits = _lexicon_hits(sentences, _RELATIONAL_LEXICON)
    findings: list[LoveAnalysisFinding] = []
    for dimension in _RELATIONAL_LEXICON:
        matched = hits.get(dimension, ())
        refs = tuple(evidence_by_sentence[item] for item in matched)
        status = "observed" if matched else "absent"
        statement = (
            f"La dynamique {dimension} apparaît dans le texte fourni."
            if matched
            else f"La dynamique {dimension} n'est pas explicitement observée."
        )
        findings.append(
            LoveAnalysisFinding(
                schema=LOVE_ANALYSIS_FINDING_SCHEMA,
                finding_ref=_finding_ref(study.study_ref, dimension, refs),
                dimension=dimension,
                statement=statement,
                status=status,
                evidence_refs=refs,
                confidence=(
                    min(0.95, 0.58 + 0.08 * len(matched))
                    if matched
                    else 0.48
                ),
                uncertainty=(
                    None
                    if matched
                    else "L'absence lexicale ne démontre pas l'absence vécue."
                ),
            )
        )
    dynamics = tuple(key for key, values in hits.items() if values)
    uncertainties: list[str] = []
    contradictions: list[str] = []
    recommendations: list[str] = []
    if "uncertainty" in source_analysis.concepts:
        uncertainties.append(
            "La première analyse signale une ambiguïté qui limite les conclusions relationnelles."
        )
    if "affection" in source_analysis.concepts and hits.get("distance"):
        contradictions.append(
            "L'affection observée coexiste avec des marqueurs de distance."
        )
    if hits.get("asymmetry") and not hits.get("reciprocity"):
        contradictions.append(
            "Des marqueurs d'asymétrie apparaissent sans réciprocité explicite."
        )
    if not hits.get("communication"):
        recommendations.append(
            "Clarifier les attentes, limites et interprétations par un dialogue explicite."
        )
    if not hits.get("reciprocity"):
        recommendations.append(
            "Ne pas conclure à la réciprocité sans élément supplémentaire."
        )
    if hits.get("conflict"):
        recommendations.append(
            "Distinguer les faits observables des interprétations lors des désaccords."
        )
    if task.capability == "love.reciprocity_analysis":
        dynamics = tuple(
            item for item in dynamics if item in {"reciprocity", "asymmetry"}
        )
    if task.capability == "love.communication_analysis":
        dynamics = tuple(
            item
            for item in dynamics
            if item in {"communication", "boundaries", "conflict"}
        )
    payload = {
        "study_ref": study.study_ref,
        "task_ref": task.task_ref,
        "capability": task.capability,
        "source_analysis_ref": source_analysis.analysis_ref,
        "dynamics": list(dynamics),
        "finding_statuses": [
            {"dimension": item.dimension, "status": item.status}
            for item in findings
        ],
        "evidence_refs": [item[0] for item in evidence],
    }
    digest = _payload_sha256(payload)
    analysis_ref = f"love-analysis:relational-dynamics:{digest[:24]}"
    artifact_ref = f"artifact:love-relational-dynamics:{digest}"
    contribution_kind = "domain_analysis"
    local_synthesis = None
    if task.capability == "recommendation.build":
        contribution_kind = "domain_analysis"
        local_synthesis = None
    return LoveRelationalDynamicsAnalysis(
        schema=LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA,
        analysis_ref=analysis_ref,
        study_ref=study.study_ref,
        specialist_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        context_revision_ref=_context_revision_ref(task),
        findings=tuple(findings),
        dynamics=dynamics,
        source_analysis_refs=(source_analysis.analysis_ref,),
        uncertainties=tuple(uncertainties),
        contradictions=tuple(contradictions),
        limitations=(
            "L'analyse porte uniquement sur le texte fourni.",
            "Elle ne constitue ni diagnostic psychologique ni synthèse globale.",
        ),
        recommendations=tuple(recommendations),
        evidence_refs=tuple(item[0] for item in evidence),
        artifact_refs=(artifact_ref,),
        local_synthesis=local_synthesis,
        contribution_kind=contribution_kind,
    )


def _build_generic_review_result(
    *,
    request: LaboratoryVisitRequest,
    task: SpecialistTaskRequest,
    source_analysis: LoveConceptAffectAnalysis,
    source_artifact: SpecialistArtifactReference,
) -> SpecialistTaskResult:
    observed = tuple(
        finding.dimension
        for finding in source_analysis.findings
        if finding.status == "observed"
    )
    payload = {
        "schema": "missipy.love.analysis_review.v1",
        "capability": task.capability,
        "source_analysis_ref": source_analysis.analysis_ref,
        "source_artifact_ref": source_artifact.artifact_ref,
        "observed_dimensions": list(observed),
        "evidence_count": len(source_analysis.evidence_refs),
        "contract_valid": True,
        "global_synthesis_claimed": False,
    }
    return SpecialistTaskResult(
        schema=SPECIALIST_TASK_RESULT_SCHEMA,
        task_ref=task.task_ref,
        plan_ref=task.plan_ref,
        specialist_ref=task.specialist_ref,
        task_type_ref=task.task_type_ref,
        capability=task.capability,
        status="completed",
        output_contract_ref=task.expected_output_contract_ref,
        human_representation=(
            "La première analyse respecte le contrat et conserve des preuves "
            "attribuées; aucune synthèse globale n'est revendiquée."
        ),
        machine_payload=payload,
        evidence_refs=source_analysis.evidence_refs,
        context_refs=task.context_refs,
        artifact_refs=(source_artifact,),
        provenance_refs=(
            request.visit_ref,
            task.task_ref,
            source_analysis.analysis_ref,
        ),
    )


def _build_first_demand(
    first_visit: LaboratoryVisitRequest,
) -> SpecialistLaboratoryMessageV2:
    payload = {
        "objective_ref": first_visit.objective_ref,
        "input_contract_ref": first_visit.input_contract_ref,
        "expected_output_contract_ref": first_visit.expected_output_contract_ref,
    }
    return SpecialistLaboratoryMessageV2(
        schema=SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA,
        message_ref=_message_ref(first_visit.visit_ref, "demand"),
        conversation_ref=first_visit.conversation_ref or "",
        visit_ref=first_visit.visit_ref,
        sequence_no=0,
        kind="demand",
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        origin_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        target_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        sender_ref=LOVE_STUDIES_LABORATORY_REF,
        recipient_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        payload_contract_ref=first_visit.input_contract_ref,
        return_route_ref=first_visit.return_route_ref,
        correlation_ref=_correlation_ref(first_visit),
        idempotency_key=stable_idempotency_key(
            first_visit.visit_ref,
            "first-demand",
        ),
        human_representation="Demande d'analyse des concepts et affects.",
        payload=payload,
        payload_sha256=compute_payload_sha256(payload),
        context_refs=first_visit.context_refs,
        evidence_refs=first_visit.evidence_refs,
    )


def _build_second_demand(
    *,
    visit: LaboratoryVisitRequest,
    task: SpecialistTaskRequest,
    first_completion: SpecialistLaboratoryMessageV2,
    first_artifact: SpecialistArtifactReference,
) -> SpecialistLaboratoryMessageV2:
    payload = {
        "task_ref": task.task_ref,
        "capability": task.capability,
        "source_analysis_ref": _source_refs(task)[0],
        "source_artifact_ref": first_artifact.artifact_ref,
        "scheduler_submission_required": True,
    }
    return SpecialistLaboratoryMessageV2(
        schema=SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA,
        message_ref=_message_ref(visit.visit_ref, "demand"),
        conversation_ref=visit.conversation_ref or "",
        visit_ref=visit.visit_ref,
        sequence_no=2,
        kind="demand",
        specialist_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        origin_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        target_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        sender_ref=LOVE_STUDIES_LABORATORY_REF,
        recipient_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        payload_contract_ref=task.input_contract_ref,
        return_route_ref=visit.return_route_ref,
        correlation_ref=first_completion.correlation_ref,
        idempotency_key=stable_idempotency_key(
            visit.visit_ref,
            "second-demand",
        ),
        human_representation=(
            "Demande d'analyse des dynamiques relationnelles à partir de "
            "l'analyse autorisée du premier spécialiste."
        ),
        payload=payload,
        payload_sha256=compute_payload_sha256(payload),
        reply_to_message_ref=first_completion.message_ref,
        parent_visit_ref=first_completion.visit_ref,
        continuation_of_message_ref=first_completion.message_ref,
        context_refs=visit.context_refs,
        evidence_refs=visit.evidence_refs,
        artifact_refs=(first_artifact,),
    )


def _resolve_task_source_artifact(
    task: SpecialistTaskRequest,
) -> SpecialistArtifactReference:
    matching = tuple(
        artifact
        for artifact in task.input_artifact_refs
        if artifact.artifact_schema == LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA
        and artifact.producer_ref == LOVE_CONCEPT_AFFECT_SPECIALIST_REF
    )
    if len(matching) != 1:
        raise NativeLoveCollaborationError(
            "second task requires exactly one concept-analysis artifact"
        )
    return matching[0]


def _validate_analysis_artifact(
    analysis: LoveConceptAffectAnalysis,
    artifact: SpecialistArtifactReference,
) -> None:
    if not isinstance(analysis, LoveConceptAffectAnalysis):
        raise TypeError("analysis must be LoveConceptAffectAnalysis")
    if not isinstance(artifact, SpecialistArtifactReference):
        raise TypeError("artifact must be SpecialistArtifactReference")
    if artifact.artifact_schema != LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA:
        raise NativeLoveCollaborationError(
            "artifact schema is not concept-affect analysis"
        )
    if artifact.producer_ref != LOVE_CONCEPT_AFFECT_SPECIALIST_REF:
        raise NativeLoveCollaborationError("artifact producer is not authorized")
    if artifact.producer_visit_ref is None:
        raise NativeLoveCollaborationError(
            "first-analysis artifact requires producer_visit_ref"
        )
    expected = _artifact_reference_for_analysis(
        analysis=analysis,
        producer_visit_ref=artifact.producer_visit_ref,
        producer_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    )
    if artifact.content_sha256 != expected.content_sha256:
        raise NativeLoveCollaborationError(
            "artifact digest does not match first analysis"
        )
    if artifact != expected:
        raise NativeLoveCollaborationError(
            "artifact metadata does not match first analysis"
        )


def _artifact_reference_for_analysis(
    *,
    analysis: LoveConceptAffectAnalysis | LoveRelationalDynamicsAnalysis,
    producer_visit_ref: str,
    producer_ref: str,
) -> SpecialistArtifactReference:
    mapping = analysis.to_mapping()
    encoded = _canonical_json_bytes(mapping)
    digest = hashlib.sha256(encoded).hexdigest()
    kind = (
        "love-concept-affect"
        if isinstance(analysis, LoveConceptAffectAnalysis)
        else "love-relational-dynamics"
    )
    return SpecialistArtifactReference(
        schema=SPECIALIST_ARTIFACT_REFERENCE_SCHEMA,
        artifact_ref=f"artifact:{kind}:{digest}",
        artifact_schema=analysis.schema,
        producer_ref=producer_ref,
        producer_visit_ref=producer_visit_ref,
        storage_ref=f"artifact:{kind}:{digest}",
        content_sha256=digest,
        media_type="application/json",
        byte_count=len(encoded),
        evidence_refs=analysis.evidence_refs,
        provenance_refs=(producer_visit_ref,),
    )


def _finding_from_mapping(value: object) -> LoveAnalysisFinding:
    if not isinstance(value, Mapping):
        raise NativeLoveCollaborationError("finding must be a mapping")
    return LoveAnalysisFinding(
        schema=str(value["schema"]),
        finding_ref=str(value["finding_ref"]),
        dimension=str(value["dimension"]),
        statement=str(value["statement"]),
        status=str(value["status"]),
        evidence_refs=_string_tuple(value.get("evidence_refs"), "evidence_refs"),
        confidence=float(value["confidence"]),
        uncertainty=_optional_text(value.get("uncertainty")),
    )


def _source_refs(task: SpecialistTaskRequest) -> tuple[str, ...]:
    value = task.metadata.get("source_analysis_ref")
    if not isinstance(value, str) or not value.startswith("love-analysis:"):
        return ()
    return (value,)


def _extract_sentences(text: str) -> tuple[str, ...]:
    values = tuple(
        part.strip()
        for part in _SENTENCE_SPLIT_RE.split(text.strip())
        if part.strip()
    )
    return values or (text.strip(),)


def _build_sentence_evidence(
    study_ref: str,
    sentences: Sequence[str],
) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for index, sentence in enumerate(sentences):
        digest = hashlib.sha256(
            f"{study_ref}|{index}|{sentence}".encode("utf-8")
        ).hexdigest()
        result.append((f"artifact:love-sentence:{digest}", sentence))
    return tuple(result)


def _lexicon_hits(
    sentences: Sequence[str],
    lexicon: Mapping[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for dimension, terms in lexicon.items():
        matched = tuple(
            sentence
            for sentence in sentences
            if any(term in _normalize_text(sentence) for term in terms)
        )
        result[dimension] = matched
    return result


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _finding_ref(
    study_ref: str,
    dimension: str,
    evidence_refs: Sequence[str],
) -> str:
    digest = hashlib.sha256(
        "|".join((study_ref, dimension, *evidence_refs)).encode("utf-8")
    ).hexdigest()
    return f"love-finding:{dimension}:{digest[:24]}"


def _context_revision_ref(task: SpecialistTaskRequest) -> str:
    value = task.metadata.get("context_revision_ref")
    if not isinstance(value, str) or not value.startswith("context-revision:"):
        raise NativeLoveCollaborationError(
            "task metadata requires context_revision_ref"
        )
    return value


def _render_relational_analysis(
    analysis: LoveRelationalDynamicsAnalysis,
) -> str:
    dynamics = ", ".join(analysis.dynamics) if analysis.dynamics else "aucune"
    lines = [
        "Analyse des dynamiques relationnelles",
        f"Dynamiques observées : {dynamics}.",
        f"Analyse source : {analysis.source_analysis_refs[0]}.",
    ]
    if analysis.contradictions:
        lines.append("Tensions : " + " ".join(analysis.contradictions))
    if analysis.uncertainties:
        lines.append("Incertitudes : " + " ".join(analysis.uncertainties))
    if analysis.recommendations:
        lines.append("Recommandations : " + " ".join(analysis.recommendations))
    lines.append("Aucune synthèse globale n'est produite à cette étape.")
    return "\n".join(lines)


def _analysis_confidence(findings: Sequence[LoveAnalysisFinding]) -> float:
    observed = tuple(
        item.confidence for item in findings if item.status == "observed"
    )
    if not observed:
        return 0.35
    return round(sum(observed) / len(observed), 4)


def _payload_sha256(payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
    if not _SHA256_RE.fullmatch(digest):
        raise AssertionError("invalid internal sha256")
    return digest


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) for item in value
    ):
        raise NativeLoveCollaborationError(
            f"{name} must be a sequence of strings"
        )
    return tuple(value)


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise NativeLoveCollaborationError("optional text must be non-empty")
    return value


def _message_ref(visit_ref: str, kind: str) -> str:
    digest = hashlib.sha256(f"{visit_ref}|{kind}".encode("utf-8")).hexdigest()
    return f"laboratory-message:{kind}:{digest[:24]}"


def _correlation_ref(visit: LaboratoryVisitRequest) -> str:
    digest = hashlib.sha256(
        f"{visit.source_candidate_ref}|{visit.conversation_ref}".encode("utf-8")
    ).hexdigest()
    return f"correlation:love-study:{digest[:24]}"


def _second_plan_ref(first_visit_ref: str) -> str:
    digest = hashlib.sha256(
        f"{first_visit_ref}|second-plan".encode("utf-8")
    ).hexdigest()
    return f"specialist-task-plan:love-collaboration:{digest[:24]}"


def _second_mission_ref(first_visit_ref: str) -> str:
    digest = hashlib.sha256(
        f"{first_visit_ref}|second-mission".encode("utf-8")
    ).hexdigest()
    return f"mission:love-collaboration:{digest[:24]}"


__all__ = (
    "CollaborativeLoveLaboratoryInputResolver",
    "InMemoryCollaborativeLoveLaboratoryInputResolver",
    "NATIVE_LOVE_COLLABORATION_PREPARATION_SCHEMA",
    "NATIVE_LOVE_COLLABORATION_RECORD_SCHEMA",
    "NATIVE_LOVE_COLLABORATION_VERSION",
    "NATIVE_LOVE_COLLABORATIVE_COMPONENT_ID",
    "NATIVE_LOVE_COLLABORATIVE_EXECUTION_SCHEMA",
    "NATIVE_LOVE_COLLABORATIVE_PROVIDER_SCHEMA",
    "NATIVE_LOVE_COLLABORATIVE_SOURCE_PATHS",
    "NativeLoveCollaborationError",
    "NativeLoveCollaborationPreparation",
    "NativeLoveCollaborationRecord",
    "NativeLoveCollaborativeExecutionRecord",
    "NativeLoveCollaborativeLaboratoryProvider",
    "build_completed_collaboration_record",
    "build_concept_analysis_artifact",
    "build_native_love_collaborative_binding_plan",
    "build_native_love_collaborative_descriptor",
    "build_native_love_collaborative_provider",
    "build_native_love_collaborative_registration",
    "build_relational_analysis_artifact",
    "concept_analysis_from_visit_result",
    "execute_native_love_collaborative_visit",
    "prepare_second_specialist_collaboration",
    "relational_analysis_from_visit_result",
    "upgrade_native_love_collaborative_registration",
)
