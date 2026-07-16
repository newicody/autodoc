"""Concrete native love laboratory and first real specialist for 0287-r7-r10.

This module attaches one content-dependent, stdlib-only specialist backend behind
an immutable Scheduler-owned runtime registration.  It does not create or run a
Scheduler, queue, EventBus, SQL/Qdrant authority, ControlProxy, model pool, or
GitHub client.

The first backend is intentionally simple but real: its output depends on the
supplied study text.  It extracts sentence-level evidence and performs bounded
concept/affect analysis.  An injected resolver keeps the provider portable; a
later SQL resolver may replace the in-memory resolver without changing the
provider or the public visit contracts.
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
    LABORATORY_VISIT_RESULT_SCHEMA,
    LaboratoryContractError,
    LaboratoryDescriptor,
    LaboratoryRegistryBindingPlan,
    LaboratoryVisitRequest,
    LaboratoryVisitResult,
    validate_laboratory_visit_result,
)
from context.love_study_contracts_0287 import (
    LOVE_ANALYSIS_FINDING_SCHEMA,
    LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
    LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
    LOVE_STUDY_REQUEST_CONTRACT_REF,
    SPECIALIST_TASK_RESULT_CONTRACT_REF,
    LOVE_STUDY_REQUEST_SCHEMA,
    LoveAnalysisFinding,
    LoveConceptAffectAnalysis,
    LoveStudyRequest,
    build_love_study_laboratory_descriptor,
)
from context.scheduler_owned_runtime_registry_0257 import (
    SchedulerOwnedRuntimeComponentRegistration,
    SchedulerOwnedRuntimeRegistry,
    validate_scheduler_owned_runtime_registry,
)
from context.specialist_laboratory_message_v2_0287 import (
    SPECIALIST_ARTIFACT_REFERENCE_SCHEMA,
    SpecialistArtifactReference,
)
from context.specialist_multitask_model_0287 import (
    SPECIALIST_TASK_REQUEST_SCHEMA,
    SPECIALIST_TASK_RESULT_SCHEMA,
    SpecialistTaskRequest,
    SpecialistTaskResult,
)

NATIVE_LOVE_LABORATORY_VERSION = "0287.r7.r10"
NATIVE_LOVE_LABORATORY_PROVIDER_SCHEMA = (
    "missipy.laboratory.provider.love_native.v1"
)
NATIVE_LOVE_LABORATORY_EXECUTION_SCHEMA = (
    "missipy.laboratory.execution.love_native.v1"
)
NATIVE_LOVE_LABORATORY_COMPONENT_ID = (
    "laboratory_provider_love_studies_local"
)
NATIVE_LOVE_LABORATORY_SOURCE_PATHS = (
    "src/context/native_love_laboratory_first_specialist_0287.py",
    "src/context/love_study_contracts_0287.py",
    "src/context/laboratory_framework_contract_0273.py",
)

_IMPLEMENTED_CAPABILITIES = frozenset(
    {
        "love.evidence_extraction",
        "love.concept_analysis",
        "love.affect_mapping",
        "analysis.local_synthesis",
    }
)
_ANALYSIS_CAPABILITIES = frozenset(
    {
        "love.concept_analysis",
        "love.affect_mapping",
        "analysis.local_synthesis",
    }
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|[\n;]+")
_WORD_RE = re.compile(r"[a-z0-9']+")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_CONCEPT_LEXICON: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "affection": (
            "amour",
            "aime",
            "aimer",
            "affection",
            "tendresse",
            "attachement",
            "cherir",
        ),
        "trust": (
            "confiance",
            "securite",
            "fiable",
            "honnete",
            "honnetete",
        ),
        "desire": (
            "desir",
            "attirance",
            "passion",
            "envie",
            "intimite",
        ),
        "reciprocity": (
            "reciproque",
            "mutuel",
            "ensemble",
            "partage",
            "partager",
        ),
        "commitment": (
            "engagement",
            "avenir",
            "projet",
            "relation",
            "couple",
        ),
        "communication": (
            "parler",
            "discussion",
            "dialogue",
            "ecouter",
            "expliquer",
            "dire",
        ),
        "boundaries": (
            "limite",
            "respect",
            "consentement",
            "besoin",
            "espace",
        ),
        "conflict": (
            "conflit",
            "dispute",
            "jalousie",
            "colere",
            "tension",
        ),
        "separation": (
            "rupture",
            "separation",
            "distance",
            "eloignement",
            "quitter",
        ),
        "uncertainty": (
            "doute",
            "incertain",
            "incertitude",
            "ambigu",
            "peur",
            "hesite",
        ),
    }
)

_AFFECT_LEXICON: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "tenderness": ("tendresse", "doux", "douce", "affection"),
        "joy": ("joie", "heureux", "heureuse", "bonheur"),
        "desire": ("desir", "attirance", "passion", "envie"),
        "fear": ("peur", "crainte", "inquiet", "inquietude"),
        "sadness": ("triste", "tristesse", "chagrin", "souffrance"),
        "anger": ("colere", "fache", "rage", "irrite"),
        "jealousy": ("jalousie", "jaloux", "jalouse"),
        "calm": ("calme", "apaise", "serenite", "paisible"),
    }
)


class NativeLoveLaboratoryError(RuntimeError):
    """Raised when the native laboratory cannot execute a bounded task."""


@runtime_checkable
class LoveLaboratoryInputResolver(Protocol):
    """Resolve authoritative study and task inputs without owning storage."""

    def resolve_study(self, request: LaboratoryVisitRequest) -> LoveStudyRequest:
        """Return the authoritative love-study request for one visit."""

    def resolve_task(self, request: LaboratoryVisitRequest) -> SpecialistTaskRequest:
        """Return the Scheduler-approved task request for one visit."""


@dataclass(frozen=True, slots=True)
class InMemoryLoveLaboratoryInputResolver:
    """Small real resolver used by tests and local smoke compositions."""

    studies: Mapping[str, LoveStudyRequest]
    tasks: Mapping[str, SpecialistTaskRequest]

    def __post_init__(self) -> None:
        studies = dict(self.studies)
        tasks = dict(self.tasks)
        if not studies or not tasks:
            raise NativeLoveLaboratoryError(
                "resolver requires at least one study and one task"
            )
        if not all(isinstance(item, LoveStudyRequest) for item in studies.values()):
            raise NativeLoveLaboratoryError("studies must contain LoveStudyRequest")
        if not all(isinstance(item, SpecialistTaskRequest) for item in tasks.values()):
            raise NativeLoveLaboratoryError(
                "tasks must contain SpecialistTaskRequest"
            )
        object.__setattr__(self, "studies", MappingProxyType(studies))
        object.__setattr__(self, "tasks", MappingProxyType(tasks))

    def resolve_study(self, request: LaboratoryVisitRequest) -> LoveStudyRequest:
        try:
            return self.studies[request.source_candidate_ref]
        except KeyError as exc:
            raise NativeLoveLaboratoryError(
                "source_candidate_ref does not resolve to a love study"
            ) from exc

    def resolve_task(self, request: LaboratoryVisitRequest) -> SpecialistTaskRequest:
        try:
            return self.tasks[request.objective_ref]
        except KeyError as exc:
            raise NativeLoveLaboratoryError(
                "objective_ref does not resolve to a specialist task"
            ) from exc


@dataclass(frozen=True, slots=True)
class NativeLoveLaboratoryExecutionRecord:
    """Handler-side proof that a real specialist processed supplied content."""

    schema: str
    provider_ref: str
    registration_component_id: str
    request: LaboratoryVisitRequest
    task: SpecialistTaskRequest
    study_ref: str
    result: LaboratoryVisitResult
    result_valid: bool
    validation_issues: tuple[str, ...] = ()
    specialist_backend_kind: str = "stdlib_lexical_v1"
    real_specialist_executed: bool = True
    content_dependent_result: bool = True
    openvino_used: bool = False
    scheduler_path_required: bool = True
    provider_owns_orchestration: bool = False
    provider_owns_persistence: bool = False
    provider_owns_vector_index: bool = False
    provider_publishes_commands: bool = False
    provider_uses_network: bool = False

    def __post_init__(self) -> None:
        if self.schema != NATIVE_LOVE_LABORATORY_EXECUTION_SCHEMA:
            raise NativeLoveLaboratoryError("unsupported native execution schema")
        if self.provider_ref != LOVE_STUDIES_LABORATORY_REF:
            raise NativeLoveLaboratoryError("unexpected native provider_ref")
        if self.registration_component_id != NATIVE_LOVE_LABORATORY_COMPONENT_ID:
            raise NativeLoveLaboratoryError("unexpected registration component")
        if self.task.task_ref != self.request.objective_ref:
            raise NativeLoveLaboratoryError("task_ref must match objective_ref")
        if self.result.visit_ref != self.request.visit_ref:
            raise NativeLoveLaboratoryError("result must belong to request")
        if self.result_valid != (not self.validation_issues):
            raise NativeLoveLaboratoryError(
                "result_valid must reflect validation_issues"
            )
        forbidden = (
            not self.real_specialist_executed,
            not self.content_dependent_result,
            not self.scheduler_path_required,
            self.provider_owns_orchestration,
            self.provider_owns_persistence,
            self.provider_owns_vector_index,
            self.provider_publishes_commands,
            self.provider_uses_network,
        )
        if any(forbidden):
            raise NativeLoveLaboratoryError(
                "native provider must preserve bounded ownership"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "provider_ref": self.provider_ref,
            "registration_component_id": self.registration_component_id,
            "request": self.request.to_mapping(),
            "task": self.task.to_mapping(),
            "study_ref": self.study_ref,
            "result": self.result.to_mapping(),
            "result_valid": self.result_valid,
            "validation_issues": list(self.validation_issues),
            "specialist_backend_kind": self.specialist_backend_kind,
            "real_specialist_executed": self.real_specialist_executed,
            "content_dependent_result": self.content_dependent_result,
            "openvino_used": self.openvino_used,
            "scheduler_path_required": self.scheduler_path_required,
            "provider_owns_orchestration": self.provider_owns_orchestration,
            "provider_owns_persistence": self.provider_owns_persistence,
            "provider_owns_vector_index": self.provider_owns_vector_index,
            "provider_publishes_commands": self.provider_publishes_commands,
            "provider_uses_network": self.provider_uses_network,
            "global_synthesis_created": False,
            "durable_write_performed": False,
            "github_mutation_performed": False,
        }


@dataclass(frozen=True, slots=True)
class NativeLoveLaboratoryProvider:
    """Native in-process provider executing the first specialist."""

    descriptor: LaboratoryDescriptor
    resolver: LoveLaboratoryInputResolver
    provider_schema: str = NATIVE_LOVE_LABORATORY_PROVIDER_SCHEMA

    def __post_init__(self) -> None:
        if self.provider_schema != NATIVE_LOVE_LABORATORY_PROVIDER_SCHEMA:
            raise NativeLoveLaboratoryError("unsupported native provider schema")
        if not isinstance(self, LaboratoryProvider):
            raise NativeLoveLaboratoryError(
                "native provider must implement LaboratoryProvider"
            )
        if self.descriptor.laboratory_ref != LOVE_STUDIES_LABORATORY_REF:
            raise NativeLoveLaboratoryError("unexpected love laboratory ref")
        if self.descriptor.provider_kind != "autodoc_native":
            raise NativeLoveLaboratoryError("provider must be autodoc_native")
        if self.descriptor.execution_boundary != "in_process":
            raise NativeLoveLaboratoryError("provider must execute in_process")
        if self.descriptor.availability != "ready" or not self.descriptor.enabled:
            raise NativeLoveLaboratoryError("provider descriptor must be ready")
        if self.descriptor.network_allowed:
            raise NativeLoveLaboratoryError("love laboratory must remain network closed")
        if not isinstance(self.resolver, LoveLaboratoryInputResolver):
            raise NativeLoveLaboratoryError(
                "resolver must implement LoveLaboratoryInputResolver"
            )

    def execute(self, request: LaboratoryVisitRequest) -> LaboratoryVisitResult:
        _validate_visit_surface(self.descriptor, request)
        study = self.resolver.resolve_study(request)
        task = self.resolver.resolve_task(request)
        _validate_resolved_inputs(request=request, study=study, task=task)
        result = _execute_first_specialist(
            request=request,
            study=study,
            task=task,
        )
        issues = validate_laboratory_visit_result(request, result)
        if issues:
            raise LaboratoryProviderExecutionError("; ".join(issues))
        return result


def build_native_love_laboratory_descriptor() -> LaboratoryDescriptor:
    """Promote the r9 descriptor to one ready native runtime surface."""

    declared = build_love_study_laboratory_descriptor()
    return replace(
        declared,
        availability="ready",
        enabled=True,
        metadata=(
            ("runtime_phase", "0287-r7-r10"),
            ("scheduler_owned_registry", "true"),
            ("first_specialist_backend", "stdlib_lexical_v1"),
            ("first_specialist_real", "true"),
            ("openvino_backend_reimplemented", "false"),
            ("global_synthesis", "later_liaison_step"),
        ),
    )


def build_native_love_laboratory_provider(
    resolver: LoveLaboratoryInputResolver,
) -> NativeLoveLaboratoryProvider:
    """Build the concrete provider with an injected input resolver."""

    return NativeLoveLaboratoryProvider(
        descriptor=build_native_love_laboratory_descriptor(),
        resolver=resolver,
    )


def build_native_love_laboratory_binding_plan() -> LaboratoryRegistryBindingPlan:
    """Build the active plan targeting the existing Scheduler-owned registry."""

    descriptor = build_native_love_laboratory_descriptor()
    return LaboratoryRegistryBindingPlan(
        schema=LABORATORY_REGISTRY_BINDING_SCHEMA,
        laboratory_ref=descriptor.laboratory_ref,
        component_id=NATIVE_LOVE_LABORATORY_COMPONENT_ID,
        capabilities=descriptor.capabilities,
        provider_source_paths=NATIVE_LOVE_LABORATORY_SOURCE_PATHS,
        ready_for_registry_attachment=True,
        provider_active=True,
    )


def build_native_love_laboratory_registration(
) -> SchedulerOwnedRuntimeComponentRegistration:
    """Convert the validated binding plan to the existing registry type."""

    plan = build_native_love_laboratory_binding_plan()
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


def bind_native_love_laboratory_registration(
    registry: SchedulerOwnedRuntimeRegistry,
) -> SchedulerOwnedRuntimeRegistry:
    """Append the provider registration immutably and idempotently."""

    registration = build_native_love_laboratory_registration()
    existing = {
        item.component_id: item for item in registry.registrations
    }.get(registration.component_id)
    if existing is not None:
        if existing == registration:
            return registry
        raise LaboratoryContractError(
            "conflicting native love laboratory registration exists"
        )
    updated = SchedulerOwnedRuntimeRegistry(
        registrations=registry.registrations + (registration,),
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
    return updated


def execute_native_love_laboratory_visit(
    request: LaboratoryVisitRequest,
    *,
    provider: NativeLoveLaboratoryProvider,
) -> NativeLoveLaboratoryExecutionRecord:
    """Execute one bounded visit through the concrete provider membrane."""

    if not isinstance(provider, NativeLoveLaboratoryProvider):
        raise TypeError("provider must be NativeLoveLaboratoryProvider")
    result = provider.execute(request)
    issues = validate_laboratory_visit_result(request, result)
    task = provider.resolver.resolve_task(request)
    study = provider.resolver.resolve_study(request)
    return NativeLoveLaboratoryExecutionRecord(
        schema=NATIVE_LOVE_LABORATORY_EXECUTION_SCHEMA,
        provider_ref=provider.descriptor.laboratory_ref,
        registration_component_id=NATIVE_LOVE_LABORATORY_COMPONENT_ID,
        request=request,
        task=task,
        study_ref=study.study_ref,
        result=result,
        result_valid=not issues,
        validation_issues=issues,
    )


def _validate_visit_surface(
    descriptor: LaboratoryDescriptor,
    request: LaboratoryVisitRequest,
) -> None:
    if request.laboratory_ref != descriptor.laboratory_ref:
        raise NativeLoveLaboratoryError("request targets another laboratory")
    if request.target_laboratory_ref != descriptor.laboratory_ref:
        raise NativeLoveLaboratoryError("target_laboratory_ref mismatch")
    if request.specialist_ref != LOVE_CONCEPT_AFFECT_SPECIALIST_REF:
        raise NativeLoveLaboratoryError(
            "r10 provider enables only the first love specialist"
        )
    if request.input_contract_ref != LOVE_STUDY_REQUEST_CONTRACT_REF:
        raise NativeLoveLaboratoryError("unsupported visit input contract")
    allowed_outputs = {
        LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
        SPECIALIST_TASK_RESULT_CONTRACT_REF,
    }
    if request.expected_output_contract_ref not in allowed_outputs:
        raise NativeLoveLaboratoryError("unsupported visit output contract")
    if request.resource_budget.allow_network:
        raise NativeLoveLaboratoryError("network-enabled visits are refused")
    if request.resource_budget.max_external_calls != 0:
        raise NativeLoveLaboratoryError("external calls are refused")


def _validate_resolved_inputs(
    *,
    request: LaboratoryVisitRequest,
    study: LoveStudyRequest,
    task: SpecialistTaskRequest,
) -> None:
    if study.schema != LOVE_STUDY_REQUEST_SCHEMA:
        raise NativeLoveLaboratoryError("resolver returned unsupported study")
    if task.schema != SPECIALIST_TASK_REQUEST_SCHEMA:
        raise NativeLoveLaboratoryError("resolver returned unsupported task")
    if task.task_ref != request.objective_ref:
        raise NativeLoveLaboratoryError("task_ref does not match objective_ref")
    if task.specialist_ref != request.specialist_ref:
        raise NativeLoveLaboratoryError("task specialist mismatch")
    if task.capability not in _IMPLEMENTED_CAPABILITIES:
        raise NativeLoveLaboratoryError("capability not implemented by r10")
    if task.input_contract_ref != request.input_contract_ref:
        raise NativeLoveLaboratoryError("task input contract mismatch")
    if task.expected_output_contract_ref != request.expected_output_contract_ref:
        raise NativeLoveLaboratoryError("task output contract mismatch")
    if task.conversation_ref != request.conversation_ref:
        raise NativeLoveLaboratoryError("task conversation mismatch")
    if task.return_route_ref != request.return_route_ref:
        raise NativeLoveLaboratoryError("task return route mismatch")
    if not set(task.context_refs).issubset(set(request.context_refs)):
        raise NativeLoveLaboratoryError("task context is not authorized by visit")
    if not set(task.evidence_refs).issubset(set(request.evidence_refs)):
        raise NativeLoveLaboratoryError("task evidence is not authorized by visit")
    if task.capability in _ANALYSIS_CAPABILITIES:
        if task.expected_output_contract_ref != (
            LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF
        ):
            raise NativeLoveLaboratoryError(
                "analysis capability requires concept-affect output"
            )
    if task.capability == "love.evidence_extraction":
        if task.expected_output_contract_ref != SPECIALIST_TASK_RESULT_CONTRACT_REF:
            raise NativeLoveLaboratoryError(
                "evidence extraction requires generic task result"
            )


def _execute_first_specialist(
    *,
    request: LaboratoryVisitRequest,
    study: LoveStudyRequest,
    task: SpecialistTaskRequest,
) -> LaboratoryVisitResult:
    sentences = _extract_sentences(study.subject_text)
    evidence = _build_sentence_evidence(sentences)
    if task.capability == "love.evidence_extraction":
        task_result = _build_evidence_task_result(
            request=request,
            task=task,
            study=study,
            evidence=evidence,
        )
        return LaboratoryVisitResult(
            schema=LABORATORY_VISIT_RESULT_SCHEMA,
            visit_ref=request.visit_ref,
            laboratory_ref=request.laboratory_ref,
            specialist_ref=request.specialist_ref,
            status="completed",
            output_contract_ref=request.expected_output_contract_ref,
            machine_result=task_result.to_mapping(),
            human_representation=task_result.human_representation,
            confidence=1.0,
            evidence_refs=task_result.evidence_refs,
            provenance_refs=(
                request.source_candidate_ref,
                request.objective_ref,
                study.study_ref,
            ),
            conversation_ref=request.conversation_ref,
            parent_visit_ref=request.parent_visit_ref,
        )
    analysis = _build_concept_affect_analysis(
        request=request,
        task=task,
        study=study,
        sentences=sentences,
        evidence=evidence,
    )
    confidence = _analysis_confidence(analysis.findings)
    human = _render_human_analysis(analysis)
    return LaboratoryVisitResult(
        schema=LABORATORY_VISIT_RESULT_SCHEMA,
        visit_ref=request.visit_ref,
        laboratory_ref=request.laboratory_ref,
        specialist_ref=request.specialist_ref,
        status="completed",
        output_contract_ref=request.expected_output_contract_ref,
        machine_result=analysis.to_mapping(),
        human_representation=human,
        confidence=confidence,
        evidence_refs=analysis.evidence_refs,
        assumptions=(
            "Analyse lexicale bornée; aucune intention absente n'est inférée.",
        ),
        provenance_refs=(
            request.source_candidate_ref,
            request.objective_ref,
            study.study_ref,
            analysis.analysis_ref,
        ),
        conversation_ref=request.conversation_ref,
        parent_visit_ref=request.parent_visit_ref,
    )


def _build_evidence_task_result(
    *,
    request: LaboratoryVisitRequest,
    task: SpecialistTaskRequest,
    study: LoveStudyRequest,
    evidence: tuple[tuple[str, str], ...],
) -> SpecialistTaskResult:
    payload = {
        "schema": "missipy.love.evidence_extraction.v1",
        "study_ref": study.study_ref,
        "sentences": [
            {"evidence_ref": evidence_ref, "text": sentence}
            for evidence_ref, sentence in evidence
        ],
        "content_dependent": True,
    }
    artifact = _artifact_reference(
        request=request,
        schema=str(payload["schema"]),
        payload=payload,
        evidence_refs=tuple(item[0] for item in evidence),
    )
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
            f"{len(evidence)} passages ont été extraits du texte fourni."
        ),
        machine_payload=payload,
        evidence_refs=tuple(item[0] for item in evidence),
        context_refs=task.context_refs,
        artifact_refs=(artifact,),
        provenance_refs=(request.visit_ref, task.task_ref),
    )


def _build_concept_affect_analysis(
    *,
    request: LaboratoryVisitRequest,
    task: SpecialistTaskRequest,
    study: LoveStudyRequest,
    sentences: tuple[str, ...],
    evidence: tuple[tuple[str, str], ...],
) -> LoveConceptAffectAnalysis:
    evidence_by_sentence = {sentence: ref for ref, sentence in evidence}
    concept_hits = _lexicon_hits(sentences, _CONCEPT_LEXICON)
    affect_hits = _lexicon_hits(sentences, _AFFECT_LEXICON)
    findings: list[LoveAnalysisFinding] = []
    for dimension in _CONCEPT_LEXICON:
        matched = concept_hits.get(dimension, ())
        status = "observed" if matched else "absent"
        refs = tuple(evidence_by_sentence[item] for item in matched)
        statement = (
            f"La dimension {dimension} apparaît dans le texte fourni."
            if matched
            else f"La dimension {dimension} n'est pas explicitement observée."
        )
        confidence = min(0.95, 0.55 + 0.1 * len(matched)) if matched else 0.5
        findings.append(
            LoveAnalysisFinding(
                schema=LOVE_ANALYSIS_FINDING_SCHEMA,
                finding_ref=_finding_ref(study.study_ref, dimension, refs),
                dimension=dimension,
                statement=statement,
                status=status,
                evidence_refs=refs,
                confidence=confidence,
                uncertainty=(
                    None
                    if matched
                    else "L'absence lexicale ne prouve pas une absence vécue."
                ),
            )
        )
    concepts = tuple(key for key, values in concept_hits.items() if values)
    affects = tuple(key for key, values in affect_hits.items() if values)
    uncertainties: list[str] = []
    contradictions: list[str] = []
    recommendations: list[str] = []
    if concept_hits.get("uncertainty"):
        uncertainties.append(
            "Le texte contient des marqueurs explicites de doute ou d'ambiguïté."
        )
    if concept_hits.get("affection") and concept_hits.get("separation"):
        contradictions.append(
            "Des marqueurs d'affection et de distance apparaissent ensemble."
        )
    if not concept_hits.get("communication"):
        recommendations.append(
            "Vérifier si les attentes et limites ont été formulées explicitement."
        )
    if not concept_hits.get("reciprocity"):
        recommendations.append(
            "Ne pas conclure à la réciprocité sans élément supplémentaire."
        )
    all_evidence = tuple(item[0] for item in evidence)
    analysis_payload = {
        "study_ref": study.study_ref,
        "task_ref": task.task_ref,
        "capability": task.capability,
        "concepts": list(concepts),
        "affects": list(affects),
        "finding_statuses": [
            {"dimension": item.dimension, "status": item.status}
            for item in findings
        ],
        "evidence_refs": list(all_evidence),
    }
    digest = _payload_sha256(analysis_payload)
    analysis_ref = f"love-analysis:concept-affect:{digest[:24]}"
    artifact_ref = f"artifact:love-concept-affect:{digest}"
    local_synthesis = None
    contribution_kind = "domain_analysis"
    if task.capability == "analysis.local_synthesis":
        contribution_kind = "local_synthesis"
        local_synthesis = _local_synthesis(concepts, affects, uncertainties)
    return LoveConceptAffectAnalysis(
        schema=LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
        analysis_ref=analysis_ref,
        study_ref=study.study_ref,
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        context_revision_ref=_context_revision_ref(task),
        findings=tuple(findings),
        concepts=concepts or ("undetermined",),
        affects=affects or ("undetermined",),
        uncertainties=tuple(uncertainties),
        contradictions=tuple(contradictions),
        limitations=(
            "Analyse lexicale déterministe sans modèle génératif.",
            "Le résultat décrit le texte fourni, pas l'intention d'une personne absente.",
        ),
        recommendations=tuple(recommendations),
        evidence_refs=all_evidence,
        artifact_refs=(artifact_ref,),
        local_synthesis=local_synthesis,
        contribution_kind=contribution_kind,
    )


def _extract_sentences(text: str) -> tuple[str, ...]:
    sentences = tuple(
        item.strip()
        for item in _SENTENCE_SPLIT_RE.split(text)
        if item.strip()
    )
    return sentences or (text.strip(),)


def _build_sentence_evidence(
    sentences: Sequence[str],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (
            f"artifact:love-evidence:{hashlib.sha256(sentence.encode('utf-8')).hexdigest()}",
            sentence,
        )
        for sentence in sentences
    )


def _lexicon_hits(
    sentences: Sequence[str],
    lexicon: Mapping[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    normalized = {sentence: _normalize_text(sentence) for sentence in sentences}
    hits: dict[str, tuple[str, ...]] = {}
    for dimension, terms in lexicon.items():
        selected = tuple(
            sentence
            for sentence, sentence_normalized in normalized.items()
            if any(_contains_term(sentence_normalized, term) for term in terms)
        )
        if selected:
            hits[dimension] = selected
    return hits


def _normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    ascii_text = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(_WORD_RE.findall(ascii_text))


def _contains_term(normalized_text: str, term: str) -> bool:
    normalized_term = _normalize_text(term)
    return f" {normalized_term} " in f" {normalized_text} "


def _finding_ref(
    study_ref: str,
    dimension: str,
    evidence_refs: Sequence[str],
) -> str:
    digest = _payload_sha256(
        {
            "study_ref": study_ref,
            "dimension": dimension,
            "evidence_refs": list(evidence_refs),
        }
    )
    return f"love-finding:{dimension}:{digest[:20]}"


def _context_revision_ref(task: SpecialistTaskRequest) -> str:
    value = str(dict(task.metadata).get("context_revision_ref", ""))
    if not value.startswith("context-revision:"):
        raise NativeLoveLaboratoryError(
            "task metadata requires context_revision_ref"
        )
    return value


def _local_synthesis(
    concepts: Sequence[str],
    affects: Sequence[str],
    uncertainties: Sequence[str],
) -> str:
    concept_text = ", ".join(concepts) if concepts else "aucun concept explicite"
    affect_text = ", ".join(affects) if affects else "aucun affect explicite"
    uncertainty_text = (
        " Une incertitude explicite reste présente."
        if uncertainties
        else ""
    )
    return (
        f"Concepts repérés : {concept_text}. Affects repérés : {affect_text}."
        f"{uncertainty_text}"
    )


def _render_human_analysis(analysis: LoveConceptAffectAnalysis) -> str:
    observed = tuple(
        finding.dimension
        for finding in analysis.findings
        if finding.status == "observed"
    )
    observed_text = ", ".join(observed) if observed else "aucune dimension explicite"
    lines = [
        "Analyse des concepts et affects",
        f"Dimensions observées : {observed_text}.",
        f"Concepts : {', '.join(analysis.concepts)}.",
        f"Affects : {', '.join(analysis.affects)}.",
    ]
    if analysis.contradictions:
        lines.append("Tensions : " + " ".join(analysis.contradictions))
    if analysis.uncertainties:
        lines.append("Incertitudes : " + " ".join(analysis.uncertainties))
    if analysis.local_synthesis:
        lines.append("Synthèse locale : " + analysis.local_synthesis)
    lines.append("Limite : aucune intention non exprimée n'est déduite.")
    return "\n".join(lines)


def _analysis_confidence(findings: Sequence[LoveAnalysisFinding]) -> float:
    observed = tuple(item.confidence for item in findings if item.status == "observed")
    if not observed:
        return 0.35
    return round(sum(observed) / len(observed), 4)


def _artifact_reference(
    *,
    request: LaboratoryVisitRequest,
    schema: str,
    payload: Mapping[str, Any],
    evidence_refs: tuple[str, ...],
) -> SpecialistArtifactReference:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return SpecialistArtifactReference(
        schema=SPECIALIST_ARTIFACT_REFERENCE_SCHEMA,
        artifact_ref=f"artifact:love-evidence-set:{digest}",
        artifact_schema=schema,
        producer_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        producer_visit_ref=request.visit_ref,
        storage_ref=f"artifact:love-evidence-set:{digest}",
        content_sha256=digest,
        media_type="application/json",
        byte_count=len(encoded),
        evidence_refs=evidence_refs,
        provenance_refs=(request.visit_ref,),
    )


def _payload_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    if not _SHA256_RE.fullmatch(digest):
        raise AssertionError("invalid internal sha256")
    return digest


__all__ = (
    "InMemoryLoveLaboratoryInputResolver",
    "LoveLaboratoryInputResolver",
    "NATIVE_LOVE_LABORATORY_COMPONENT_ID",
    "NATIVE_LOVE_LABORATORY_EXECUTION_SCHEMA",
    "NATIVE_LOVE_LABORATORY_PROVIDER_SCHEMA",
    "NATIVE_LOVE_LABORATORY_SOURCE_PATHS",
    "NATIVE_LOVE_LABORATORY_VERSION",
    "NativeLoveLaboratoryError",
    "NativeLoveLaboratoryExecutionRecord",
    "NativeLoveLaboratoryProvider",
    "bind_native_love_laboratory_registration",
    "build_native_love_laboratory_binding_plan",
    "build_native_love_laboratory_descriptor",
    "build_native_love_laboratory_provider",
    "build_native_love_laboratory_registration",
    "execute_native_love_laboratory_visit",
)
