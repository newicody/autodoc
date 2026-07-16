"""Love-study domain contracts and portable descriptors for 0287-r7-r9.

This module declares a concrete future laboratory surface and two extensible,
multitask specialist definitions.  It remains contract-only: it does not
instantiate a provider, attach task handlers, schedule visits, call OpenVINO,
write SQL/Qdrant, publish EventBus events, touch ControlProxy, or mutate GitHub.

The specialists primarily produce deep domain analyses.  Local synthesis is an
explicit task type; global mutualized synthesis remains a later liaison step.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import re
from types import MappingProxyType
from typing import Any, Literal

from context.laboratory_framework_contract_0273 import (
    LABORATORY_DESCRIPTOR_SCHEMA,
    LaboratoryDescriptor,
)
from context.portable_specialist_contract_0284 import (
    PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
    SPECIALIST_CAPABILITY_SCHEMA,
    SPECIALIST_EXECUTION_PROFILE_SCHEMA,
    SPECIALIST_LABORATORY_BINDING_SCHEMA,
    PortableSpecialistDescriptor,
    SpecialistCapabilityContract,
    SpecialistExecutionProfile,
    SpecialistLaboratoryBinding,
)
from context.specialist_multitask_model_0287 import (
    EXTENSIBLE_MULTITASK_SPECIALIST_SCHEMA,
    SPECIALIST_TASK_TYPE_SCHEMA,
    ExtensibleMultitaskSpecialistDefinition,
    SpecialistTaskType,
)

LOVE_STUDY_CONTRACT_VERSION = "0287.r7.r9"
LOVE_STUDY_REQUEST_SCHEMA = "missipy.love.study_request.v1"
LOVE_ANALYSIS_FINDING_SCHEMA = "missipy.love.analysis_finding.v1"
LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA = (
    "missipy.love.concept_affect_analysis.v1"
)
LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA = (
    "missipy.love.relational_dynamics_analysis.v1"
)
LOVE_STUDY_RESULT_SCHEMA = "missipy.love.study_result.v1"
LOVE_STUDY_PROTOTYPE_DEFINITION_SCHEMA = (
    "missipy.love.prototype_definition.v1"
)

LOVE_STUDY_REQUEST_CONTRACT_REF = (
    "contract:missipy.love.study_request.v1"
)
LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF = (
    "contract:missipy.love.concept_affect_analysis.v1"
)
LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF = (
    "contract:missipy.love.relational_dynamics_analysis.v1"
)
LOVE_STUDY_RESULT_CONTRACT_REF = (
    "contract:missipy.love.study_result.v1"
)
SPECIALIST_TASK_RESULT_CONTRACT_REF = (
    "contract:missipy.specialist.task_result.v1"
)
SPECIALIST_MESSAGE_V2_CONTRACT_REF = (
    "contract:missipy.specialist.laboratory_message.v2"
)

LOVE_STUDIES_LABORATORY_REF = "laboratory:love-studies-local"
LOVE_CONCEPT_AFFECT_SPECIALIST_REF = (
    "specialist:love-concept-and-affect-analyst"
)
LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF = (
    "specialist:love-relational-dynamics-analyst"
)

LoveFindingStatus = Literal[
    "observed",
    "inferred",
    "absent",
    "contradicted",
]
LoveStudyStatus = Literal[
    "analyses_ready",
    "needs_context",
    "failed",
    "synthesized",
]

_ALLOWED_FINDING_STATUSES = frozenset(
    {"observed", "inferred", "absent", "contradicted"}
)
_ALLOWED_STUDY_STATUSES = frozenset(
    {"analyses_ready", "needs_context", "failed", "synthesized"}
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_.-]+$")
_STUDY_PREFIXES = ("love-study:",)
_ANALYSIS_PREFIXES = ("love-analysis:",)
_RESULT_PREFIXES = ("love-study-result:",)
_ISSUE_PREFIXES = ("github-issue:", "issue:")
_CONTEXT_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "qdrant:",
    "artifact:",
    "dataset:",
    "research-work-package:",
    "context-revision:",
)
_EVIDENCE_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "artifact:",
    "dataset:",
    "validation:",
)
_ARTIFACT_PREFIXES = ("artifact:", "sql:", "dataset:")
_SYNTHESIS_PREFIXES = ("specialist-liaison-synthesis:",)
_FINAL_ARTIFACT_PREFIXES = ("final-artifact:", "artifact:")
_MAX_ITEMS = 1_024
_MAX_TEXT_CHARS = 1_000_000
_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))


class LoveStudyContractError(ValueError):
    """Raised when one love-study contract is incoherent."""


@dataclass(frozen=True, slots=True)
class LoveStudyRequest:
    """Authoritative domain request transmitted to the specialist tasks."""

    schema: str
    study_ref: str
    source_issue_ref: str
    objective: str
    subject_text: str
    constraints: tuple[str, ...]
    success_criteria: tuple[str, ...]
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    requested_specialist_refs: tuple[str, ...] = (
        LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
    )
    language: str = "fr"
    synthesis_policy: str = "liaison_after_domain_analyses"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != LOVE_STUDY_REQUEST_SCHEMA:
            raise LoveStudyContractError("unsupported love study request schema")
        _require_ref("study_ref", self.study_ref, _STUDY_PREFIXES)
        _require_ref("source_issue_ref", self.source_issue_ref, _ISSUE_PREFIXES)
        _require_text("objective", self.objective)
        _require_text("subject_text", self.subject_text)
        object.__setattr__(
            self,
            "constraints",
            _normalize_texts("constraints", self.constraints),
        )
        object.__setattr__(
            self,
            "success_criteria",
            _normalize_texts("success_criteria", self.success_criteria),
        )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs("context_refs", self.context_refs, _CONTEXT_PREFIXES),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs", self.evidence_refs, _EVIDENCE_PREFIXES
            ),
        )
        specialists = _normalize_refs(
            "requested_specialist_refs",
            self.requested_specialist_refs,
            ("specialist:",),
        )
        expected = {
            LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
            LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        }
        if set(specialists) != expected:
            raise LoveStudyContractError(
                "requested_specialist_refs must declare both prototype specialists"
            )
        object.__setattr__(self, "requested_specialist_refs", specialists)
        if not isinstance(self.language, str) or not re.fullmatch(
            r"[a-z]{2,3}(?:-[A-Z]{2})?", self.language
        ):
            raise LoveStudyContractError("language must be a language tag")
        if self.synthesis_policy != "liaison_after_domain_analyses":
            raise LoveStudyContractError("unsupported synthesis_policy")
        object.__setattr__(self, "metadata", _freeze_json(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "study_ref": self.study_ref,
            "source_issue_ref": self.source_issue_ref,
            "objective": self.objective,
            "subject_text": self.subject_text,
            "constraints": list(self.constraints),
            "success_criteria": list(self.success_criteria),
            "context_refs": list(self.context_refs),
            "evidence_refs": list(self.evidence_refs),
            "requested_specialist_refs": list(self.requested_specialist_refs),
            "language": self.language,
            "synthesis_policy": self.synthesis_policy,
            "metadata": _thaw_json(self.metadata),
            "request_authoritative": True,
            "global_synthesis_created": False,
            "scheduler_route_created": False,
        }


@dataclass(frozen=True, slots=True)
class LoveAnalysisFinding:
    """One attributable finding supported by explicit evidence references."""

    schema: str
    finding_ref: str
    dimension: str
    statement: str
    status: LoveFindingStatus
    evidence_refs: tuple[str, ...]
    confidence: float
    uncertainty: str | None = None

    def __post_init__(self) -> None:
        if self.schema != LOVE_ANALYSIS_FINDING_SCHEMA:
            raise LoveStudyContractError("unsupported love finding schema")
        _require_ref("finding_ref", self.finding_ref, ("love-finding:",))
        _require_identifier("dimension", self.dimension)
        _require_text("statement", self.statement)
        if self.status not in _ALLOWED_FINDING_STATUSES:
            raise LoveStudyContractError("unsupported finding status")
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs",
                self.evidence_refs,
                _EVIDENCE_PREFIXES,
                allow_empty=self.status == "absent",
            ),
        )
        if isinstance(self.confidence, bool) or not isinstance(
            self.confidence, (int, float)
        ):
            raise LoveStudyContractError("confidence must be numeric")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise LoveStudyContractError("confidence must be between 0 and 1")
        object.__setattr__(self, "confidence", float(self.confidence))
        if self.uncertainty is not None:
            _require_text("uncertainty", self.uncertainty)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "finding_ref": self.finding_ref,
            "dimension": self.dimension,
            "statement": self.statement,
            "status": self.status,
            "evidence_refs": list(self.evidence_refs),
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
        }


@dataclass(frozen=True, slots=True)
class LoveConceptAffectAnalysis:
    """Deep concept and affect analysis from the first specialist."""

    schema: str
    analysis_ref: str
    study_ref: str
    specialist_ref: str
    context_revision_ref: str
    findings: tuple[LoveAnalysisFinding, ...]
    concepts: tuple[str, ...]
    affects: tuple[str, ...]
    uncertainties: tuple[str, ...]
    contradictions: tuple[str, ...]
    limitations: tuple[str, ...]
    recommendations: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    artifact_refs: tuple[str, ...]
    local_synthesis: str | None = None
    contribution_kind: str = "domain_analysis"

    def __post_init__(self) -> None:
        _validate_analysis_common(
            schema=self.schema,
            expected_schema=LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
            analysis_ref=self.analysis_ref,
            study_ref=self.study_ref,
            specialist_ref=self.specialist_ref,
            expected_specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
            context_revision_ref=self.context_revision_ref,
            findings=self.findings,
            uncertainties=self.uncertainties,
            contradictions=self.contradictions,
            limitations=self.limitations,
            recommendations=self.recommendations,
            evidence_refs=self.evidence_refs,
            artifact_refs=self.artifact_refs,
            local_synthesis=self.local_synthesis,
            contribution_kind=self.contribution_kind,
        )
        object.__setattr__(self, "findings", tuple(self.findings))
        object.__setattr__(self, "concepts", _normalize_identifiers("concepts", self.concepts))
        object.__setattr__(self, "affects", _normalize_identifiers("affects", self.affects))
        _freeze_analysis_common(self)

    def to_mapping(self) -> dict[str, object]:
        return _analysis_mapping(
            self,
            domain_fields={"concepts": list(self.concepts), "affects": list(self.affects)},
        )


@dataclass(frozen=True, slots=True)
class LoveRelationalDynamicsAnalysis:
    """Deep relational-dynamics analysis from the second specialist."""

    schema: str
    analysis_ref: str
    study_ref: str
    specialist_ref: str
    context_revision_ref: str
    findings: tuple[LoveAnalysisFinding, ...]
    dynamics: tuple[str, ...]
    source_analysis_refs: tuple[str, ...]
    uncertainties: tuple[str, ...]
    contradictions: tuple[str, ...]
    limitations: tuple[str, ...]
    recommendations: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    artifact_refs: tuple[str, ...]
    local_synthesis: str | None = None
    contribution_kind: str = "domain_analysis"

    def __post_init__(self) -> None:
        _validate_analysis_common(
            schema=self.schema,
            expected_schema=LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA,
            analysis_ref=self.analysis_ref,
            study_ref=self.study_ref,
            specialist_ref=self.specialist_ref,
            expected_specialist_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
            context_revision_ref=self.context_revision_ref,
            findings=self.findings,
            uncertainties=self.uncertainties,
            contradictions=self.contradictions,
            limitations=self.limitations,
            recommendations=self.recommendations,
            evidence_refs=self.evidence_refs,
            artifact_refs=self.artifact_refs,
            local_synthesis=self.local_synthesis,
            contribution_kind=self.contribution_kind,
        )
        object.__setattr__(self, "findings", tuple(self.findings))
        object.__setattr__(
            self,
            "dynamics",
            _normalize_identifiers("dynamics", self.dynamics),
        )
        source_refs = _normalize_refs(
            "source_analysis_refs", self.source_analysis_refs, _ANALYSIS_PREFIXES
        )
        if not source_refs:
            raise LoveStudyContractError(
                "relational dynamics analysis requires a source analysis"
            )
        object.__setattr__(self, "source_analysis_refs", source_refs)
        _freeze_analysis_common(self)

    def to_mapping(self) -> dict[str, object]:
        return _analysis_mapping(
            self,
            domain_fields={
                "dynamics": list(self.dynamics),
                "source_analysis_refs": list(self.source_analysis_refs),
            },
        )


@dataclass(frozen=True, slots=True)
class LoveStudyResult:
    """Versioned result index before or after the distinct liaison synthesis."""

    schema: str
    result_ref: str
    study_ref: str
    status: LoveStudyStatus
    context_revision_ref: str
    concept_affect_analysis_ref: str
    relational_dynamics_analysis_ref: str
    unresolved_points: tuple[str, ...]
    liaison_synthesis_ref: str | None = None
    final_artifact_ref: str | None = None

    def __post_init__(self) -> None:
        if self.schema != LOVE_STUDY_RESULT_SCHEMA:
            raise LoveStudyContractError("unsupported love study result schema")
        _require_ref("result_ref", self.result_ref, _RESULT_PREFIXES)
        _require_ref("study_ref", self.study_ref, _STUDY_PREFIXES)
        if self.status not in _ALLOWED_STUDY_STATUSES:
            raise LoveStudyContractError("unsupported love study result status")
        _require_ref(
            "context_revision_ref",
            self.context_revision_ref,
            ("context-revision:",),
        )
        _require_ref(
            "concept_affect_analysis_ref",
            self.concept_affect_analysis_ref,
            _ANALYSIS_PREFIXES,
        )
        _require_ref(
            "relational_dynamics_analysis_ref",
            self.relational_dynamics_analysis_ref,
            _ANALYSIS_PREFIXES,
        )
        object.__setattr__(
            self,
            "unresolved_points",
            _normalize_texts(
                "unresolved_points", self.unresolved_points, allow_empty=True
            ),
        )
        if self.liaison_synthesis_ref is not None:
            _require_ref(
                "liaison_synthesis_ref",
                self.liaison_synthesis_ref,
                _SYNTHESIS_PREFIXES,
            )
        if self.final_artifact_ref is not None:
            _require_ref(
                "final_artifact_ref",
                self.final_artifact_ref,
                _FINAL_ARTIFACT_PREFIXES,
            )
        if self.status == "synthesized":
            if self.liaison_synthesis_ref is None or self.final_artifact_ref is None:
                raise LoveStudyContractError(
                    "synthesized result requires liaison and final artifact refs"
                )
        elif self.liaison_synthesis_ref is not None or self.final_artifact_ref is not None:
            raise LoveStudyContractError(
                "only synthesized results may reference final synthesis artifacts"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "result_ref": self.result_ref,
            "study_ref": self.study_ref,
            "status": self.status,
            "context_revision_ref": self.context_revision_ref,
            "concept_affect_analysis_ref": self.concept_affect_analysis_ref,
            "relational_dynamics_analysis_ref": self.relational_dynamics_analysis_ref,
            "unresolved_points": list(self.unresolved_points),
            "liaison_synthesis_ref": self.liaison_synthesis_ref,
            "final_artifact_ref": self.final_artifact_ref,
            "global_synthesis_complete": self.status == "synthesized",
        }


@dataclass(frozen=True, slots=True)
class LoveStudyPrototypeDefinition:
    """Contract-only assembly of one laboratory and two specialists."""

    schema: str
    laboratory: LaboratoryDescriptor
    specialists: tuple[ExtensibleMultitaskSpecialistDefinition, ...]

    def __post_init__(self) -> None:
        if self.schema != LOVE_STUDY_PROTOTYPE_DEFINITION_SCHEMA:
            raise LoveStudyContractError("unsupported prototype definition schema")
        if not isinstance(self.laboratory, LaboratoryDescriptor):
            raise LoveStudyContractError("laboratory must be LaboratoryDescriptor")
        if self.laboratory.laboratory_ref != LOVE_STUDIES_LABORATORY_REF:
            raise LoveStudyContractError("unexpected love-study laboratory_ref")
        if self.laboratory.provider_kind != "autodoc_native":
            raise LoveStudyContractError("love-study laboratory must be autodoc_native")
        if self.laboratory.enabled or self.laboratory.availability != "declared":
            raise LoveStudyContractError(
                "contract-only laboratory must remain declared and disabled"
            )
        specialists = tuple(self.specialists)
        if len(specialists) != 2 or not all(
            isinstance(item, ExtensibleMultitaskSpecialistDefinition)
            for item in specialists
        ):
            raise LoveStudyContractError(
                "prototype must declare exactly two multitask specialists"
            )
        refs = {item.descriptor.specialist_ref for item in specialists}
        expected = {
            LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
            LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        }
        if refs != expected:
            raise LoveStudyContractError("unexpected prototype specialist set")
        laboratory_capabilities = set(self.laboratory.capabilities)
        for definition in specialists:
            binding = definition.descriptor.laboratory_bindings[0]
            if binding.laboratory_ref != self.laboratory.laboratory_ref:
                raise LoveStudyContractError("specialist binding laboratory mismatch")
            if not set(binding.required_laboratory_capabilities).issubset(
                laboratory_capabilities
            ):
                raise LoveStudyContractError(
                    "laboratory does not satisfy specialist requirements"
                )
        object.__setattr__(self, "specialists", specialists)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "laboratory": self.laboratory.to_mapping(),
            "specialists": [item.to_mapping() for item in self.specialists],
            "provider_instantiated": False,
            "task_handlers_attached": False,
            "scheduler_registration_performed": False,
            "openvino_runtime_loaded": False,
            "global_synthesis_created": False,
        }


def build_love_study_laboratory_descriptor() -> LaboratoryDescriptor:
    """Return the disabled descriptor for the future concrete native laboratory."""

    return LaboratoryDescriptor(
        schema=LABORATORY_DESCRIPTOR_SCHEMA,
        laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        provider_kind="autodoc_native",
        display_name="Love studies local laboratory",
        capabilities=(
            "specialist.multitask_execution",
            "specialist.message_v2",
            "artifact.digest_addressed",
            "context.revision_binding",
            "openvino.runtime_reuse",
            "analysis.liaison_ready",
        ),
        accepted_input_contract_refs=(
            LOVE_STUDY_REQUEST_CONTRACT_REF,
            SPECIALIST_MESSAGE_V2_CONTRACT_REF,
        ),
        produced_output_contract_refs=(
            LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
            LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF,
            LOVE_STUDY_RESULT_CONTRACT_REF,
            SPECIALIST_TASK_RESULT_CONTRACT_REF,
            SPECIALIST_MESSAGE_V2_CONTRACT_REF,
        ),
        execution_boundary="in_process",
        availability="declared",
        enabled=False,
        network_allowed=False,
        metadata=(
            ("runtime_phase", "0287-r7-r10"),
            ("scheduler_owned_registry", "true"),
            ("global_synthesis", "later_liaison_step"),
        ),
    )


def build_love_concept_affect_specialist_definition(
) -> ExtensibleMultitaskSpecialistDefinition:
    """Declare the first multitask specialist without attaching handlers."""

    capabilities = (
        _capability(
            "love.evidence_extraction",
            "Extract attributable evidence for later concept and affect analysis.",
            (LOVE_STUDY_REQUEST_CONTRACT_REF,),
            (SPECIALIST_TASK_RESULT_CONTRACT_REF,),
        ),
        _capability(
            "love.concept_analysis",
            "Analyse concepts and representations of love in the supplied material.",
            (LOVE_STUDY_REQUEST_CONTRACT_REF,),
            (LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,),
        ),
        _capability(
            "love.affect_mapping",
            "Map expressed affects, absences, tensions and uncertainty.",
            (LOVE_STUDY_REQUEST_CONTRACT_REF,),
            (LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,),
        ),
        _capability(
            "analysis.compare",
            "Compare compatible concept and affect analyses.",
            (LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,),
            (LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,),
        ),
        _capability(
            "analysis.critique",
            "Critique evidence alignment and unsupported interpretations.",
            (LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,),
            (SPECIALIST_TASK_RESULT_CONTRACT_REF,),
        ),
        _capability(
            "analysis.local_synthesis",
            "Produce a local synthesis only when explicitly requested.",
            (LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,),
            (LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,),
        ),
    )
    descriptor = _descriptor(
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        display_name="Love concept and affect analyst",
        capabilities=capabilities,
    )
    task_types = tuple(
        _task_type(
            task_type_ref=f"task-type:{capability.capability}",
            capability=capability,
            contribution_kind=(
                "local_synthesis"
                if capability.capability == "analysis.local_synthesis"
                else "domain_analysis"
            ),
        )
        for capability in capabilities
    )
    return ExtensibleMultitaskSpecialistDefinition(
        schema=EXTENSIBLE_MULTITASK_SPECIALIST_SCHEMA,
        descriptor=descriptor,
        task_types=task_types,
    )


def build_love_relational_dynamics_specialist_definition(
) -> ExtensibleMultitaskSpecialistDefinition:
    """Declare the second multitask specialist without attaching handlers."""

    analysis_inputs = (
        LOVE_STUDY_REQUEST_CONTRACT_REF,
        LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
    )
    capabilities = (
        _capability(
            "love.relational_dynamics",
            "Analyse relational dynamics without inferring unavailable intentions.",
            analysis_inputs,
            (LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF,),
        ),
        _capability(
            "love.reciprocity_analysis",
            "Analyse reciprocity, asymmetries and unresolved expectations.",
            analysis_inputs,
            (LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF,),
        ),
        _capability(
            "love.communication_analysis",
            "Analyse communication, explicit limits and missing clarification.",
            analysis_inputs,
            (LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF,),
        ),
        _capability(
            "analysis.critique",
            "Critique another authorized analysis while preserving provenance.",
            (LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,),
            (SPECIALIST_TASK_RESULT_CONTRACT_REF,),
        ),
        _capability(
            "analysis.validate",
            "Validate contract compliance and evidence alignment.",
            (
                LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
                LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF,
            ),
            (SPECIALIST_TASK_RESULT_CONTRACT_REF,),
        ),
        _capability(
            "recommendation.build",
            "Build bounded recommendations from validated domain analyses.",
            (
                LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
                LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF,
            ),
            (LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF,),
        ),
    )
    descriptor = _descriptor(
        specialist_ref=LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
        display_name="Love relational dynamics analyst",
        capabilities=capabilities,
    )
    task_types = tuple(
        _task_type(
            task_type_ref=f"task-type:{capability.capability}",
            capability=capability,
            contribution_kind=(
                "recommendation"
                if capability.capability == "recommendation.build"
                else "domain_analysis"
            ),
        )
        for capability in capabilities
    )
    return ExtensibleMultitaskSpecialistDefinition(
        schema=EXTENSIBLE_MULTITASK_SPECIALIST_SCHEMA,
        descriptor=descriptor,
        task_types=task_types,
    )


def build_love_study_prototype_definition() -> LoveStudyPrototypeDefinition:
    """Build the complete contract-only prototype declaration."""

    return LoveStudyPrototypeDefinition(
        schema=LOVE_STUDY_PROTOTYPE_DEFINITION_SCHEMA,
        laboratory=build_love_study_laboratory_descriptor(),
        specialists=(
            build_love_concept_affect_specialist_definition(),
            build_love_relational_dynamics_specialist_definition(),
        ),
    )


def _capability(
    capability: str,
    description: str,
    inputs: tuple[str, ...],
    outputs: tuple[str, ...],
) -> SpecialistCapabilityContract:
    return SpecialistCapabilityContract(
        schema=SPECIALIST_CAPABILITY_SCHEMA,
        capability=capability,
        description=description,
        accepted_input_contract_refs=inputs,
        produced_output_contract_refs=outputs,
    )


def _descriptor(
    *,
    specialist_ref: str,
    display_name: str,
    capabilities: tuple[SpecialistCapabilityContract, ...],
) -> PortableSpecialistDescriptor:
    inputs = tuple(
        dict.fromkeys(
            contract_ref
            for capability in capabilities
            for contract_ref in capability.accepted_input_contract_refs
        )
    )
    outputs = tuple(
        dict.fromkeys(
            contract_ref
            for capability in capabilities
            for contract_ref in capability.produced_output_contract_refs
        )
    )
    return PortableSpecialistDescriptor(
        schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
        specialist_ref=specialist_ref,
        display_name=display_name,
        specialist_version="1.0.0",
        capabilities=capabilities,
        accepted_input_contract_refs=inputs,
        produced_output_contract_refs=outputs,
        execution_profile=SpecialistExecutionProfile(
            schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
            preferred_execution_boundaries=("in_process",),
            determinism_preference="preferred",
            max_parallel_visits=2,
            network_allowed=False,
            max_external_calls_per_visit=0,
            accelerator_required=False,
            preferred_device_refs=("device:CPU", "openvino:GPU"),
            metadata=(("openvino_reuse", "required"),),
        ),
        laboratory_bindings=(
            SpecialistLaboratoryBinding(
                schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
                specialist_ref=specialist_ref,
                laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
                visit_modes=("resident", "visitor"),
                required_laboratory_capabilities=(
                    "specialist.multitask_execution",
                    "specialist.message_v2",
                    "artifact.digest_addressed",
                    "context.revision_binding",
                    "openvino.runtime_reuse",
                ),
                priority=10,
            ),
        ),
        availability="declared",
        metadata=(
            ("primary_output", "deep_domain_analysis"),
            ("global_synthesis", "later_liaison_step"),
            ("runtime_phase", "0287-r7-r10"),
        ),
    )


def _task_type(
    *,
    task_type_ref: str,
    capability: SpecialistCapabilityContract,
    contribution_kind: str,
) -> SpecialistTaskType:
    return SpecialistTaskType(
        schema=SPECIALIST_TASK_TYPE_SCHEMA,
        task_type_ref=task_type_ref,
        capability=capability.capability,
        description=capability.description,
        accepted_input_contract_refs=capability.accepted_input_contract_refs,
        produced_output_contract_refs=capability.produced_output_contract_refs,
        contribution_kinds=(contribution_kind,),
        supports_batch=False,
        supports_resume=True,
        supports_review=True,
        deterministic=False,
        metadata={
            "scheduler_owned": True,
            "handler_attached": False,
        },
    )


def _validate_analysis_common(
    *,
    schema: str,
    expected_schema: str,
    analysis_ref: str,
    study_ref: str,
    specialist_ref: str,
    expected_specialist_ref: str,
    context_revision_ref: str,
    findings: Sequence[LoveAnalysisFinding],
    uncertainties: Sequence[str],
    contradictions: Sequence[str],
    limitations: Sequence[str],
    recommendations: Sequence[str],
    evidence_refs: Sequence[str],
    artifact_refs: Sequence[str],
    local_synthesis: str | None,
    contribution_kind: str,
) -> None:
    if schema != expected_schema:
        raise LoveStudyContractError("unsupported love analysis schema")
    _require_ref("analysis_ref", analysis_ref, _ANALYSIS_PREFIXES)
    _require_ref("study_ref", study_ref, _STUDY_PREFIXES)
    if specialist_ref != expected_specialist_ref:
        raise LoveStudyContractError("analysis specialist_ref is not authorized")
    _require_ref("specialist_ref", specialist_ref, ("specialist:",))
    _require_ref(
        "context_revision_ref", context_revision_ref, ("context-revision:",)
    )
    values = tuple(findings)
    if not values or not all(isinstance(item, LoveAnalysisFinding) for item in values):
        raise LoveStudyContractError("findings must contain LoveAnalysisFinding values")
    if contribution_kind not in {"domain_analysis", "local_synthesis"}:
        raise LoveStudyContractError("unsupported contribution_kind")
    if contribution_kind == "local_synthesis" and local_synthesis is None:
        raise LoveStudyContractError("local_synthesis contribution requires text")
    if local_synthesis is not None:
        _require_text("local_synthesis", local_synthesis)
    _normalize_texts("uncertainties", uncertainties, allow_empty=True)
    _normalize_texts("contradictions", contradictions, allow_empty=True)
    _normalize_texts("limitations", limitations, allow_empty=True)
    _normalize_texts("recommendations", recommendations, allow_empty=True)
    _normalize_refs("evidence_refs", evidence_refs, _EVIDENCE_PREFIXES)
    _normalize_refs("artifact_refs", artifact_refs, _ARTIFACT_PREFIXES)


def _freeze_analysis_common(value: object) -> None:
    for name in (
        "uncertainties",
        "contradictions",
        "limitations",
        "recommendations",
    ):
        object.__setattr__(
            value,
            name,
            _normalize_texts(name, getattr(value, name), allow_empty=True),
        )
    object.__setattr__(
        value,
        "evidence_refs",
        _normalize_refs("evidence_refs", getattr(value, "evidence_refs"), _EVIDENCE_PREFIXES),
    )
    object.__setattr__(
        value,
        "artifact_refs",
        _normalize_refs("artifact_refs", getattr(value, "artifact_refs"), _ARTIFACT_PREFIXES),
    )


def _analysis_mapping(value: object, *, domain_fields: Mapping[str, object]) -> dict[str, object]:
    mapping = {
        "schema": getattr(value, "schema"),
        "analysis_ref": getattr(value, "analysis_ref"),
        "study_ref": getattr(value, "study_ref"),
        "specialist_ref": getattr(value, "specialist_ref"),
        "context_revision_ref": getattr(value, "context_revision_ref"),
        "findings": [item.to_mapping() for item in getattr(value, "findings")],
        "uncertainties": list(getattr(value, "uncertainties")),
        "contradictions": list(getattr(value, "contradictions")),
        "limitations": list(getattr(value, "limitations")),
        "recommendations": list(getattr(value, "recommendations")),
        "evidence_refs": list(getattr(value, "evidence_refs")),
        "artifact_refs": list(getattr(value, "artifact_refs")),
        "local_synthesis": getattr(value, "local_synthesis"),
        "contribution_kind": getattr(value, "contribution_kind"),
        "global_synthesis_claimed": False,
    }
    mapping.update(domain_fields)
    return mapping


def _require_ref(name: str, value: str, prefixes: tuple[str, ...]) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise LoveStudyContractError(f"{name} must be a typed reference")
    if not value.startswith(prefixes):
        raise LoveStudyContractError(
            f"{name} must start with one of: {', '.join(prefixes)}"
        )


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise LoveStudyContractError(f"{name} must be non-empty")
    if len(value) > _MAX_TEXT_CHARS:
        raise LoveStudyContractError(f"{name} is too large")


def _require_identifier(name: str, value: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER_RE.match(value):
        raise LoveStudyContractError(f"{name} must be a dotted identifier")


def _normalize_refs(
    name: str,
    values: Sequence[str],
    prefixes: tuple[str, ...],
    *,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    refs = tuple(values)
    if len(refs) > _MAX_ITEMS:
        raise LoveStudyContractError(f"{name} contains too many values")
    if not refs and not allow_empty:
        raise LoveStudyContractError(f"{name} must not be empty")
    for ref in refs:
        _require_ref(name, ref, prefixes)
    if len(set(refs)) != len(refs):
        raise LoveStudyContractError(f"{name} must contain unique values")
    return refs


def _normalize_texts(
    name: str,
    values: Sequence[str],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    texts = tuple(values)
    if len(texts) > _MAX_ITEMS:
        raise LoveStudyContractError(f"{name} contains too many values")
    if not texts and not allow_empty:
        raise LoveStudyContractError(f"{name} must not be empty")
    for text in texts:
        _require_text(name, text)
    return texts


def _normalize_identifiers(name: str, values: Sequence[str]) -> tuple[str, ...]:
    identifiers = tuple(values)
    if not identifiers:
        raise LoveStudyContractError(f"{name} must not be empty")
    for value in identifiers:
        _require_identifier(name, value)
    if len(set(identifiers)) != len(identifiers):
        raise LoveStudyContractError(f"{name} must contain unique values")
    return identifiers


def _freeze_json(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LoveStudyContractError("metadata must be a mapping")
    return MappingProxyType(
        {str(key): _freeze_json_value(item) for key, item in value.items()}
    )


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, _JSON_SCALAR_TYPES):
        return value
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json_value(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json_value(item) for item in value)
    raise LoveStudyContractError("metadata must contain JSON-compatible values")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


__all__ = [
    "LOVE_ANALYSIS_FINDING_SCHEMA",
    "LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF",
    "LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA",
    "LOVE_CONCEPT_AFFECT_SPECIALIST_REF",
    "LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF",
    "LOVE_RELATIONAL_DYNAMICS_ANALYSIS_SCHEMA",
    "LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF",
    "LOVE_STUDIES_LABORATORY_REF",
    "LOVE_STUDY_PROTOTYPE_DEFINITION_SCHEMA",
    "LOVE_STUDY_REQUEST_CONTRACT_REF",
    "LOVE_STUDY_REQUEST_SCHEMA",
    "LOVE_STUDY_RESULT_CONTRACT_REF",
    "LOVE_STUDY_RESULT_SCHEMA",
    "LoveAnalysisFinding",
    "LoveConceptAffectAnalysis",
    "LoveRelationalDynamicsAnalysis",
    "LoveStudyContractError",
    "LoveStudyPrototypeDefinition",
    "LoveStudyRequest",
    "LoveStudyResult",
    "build_love_concept_affect_specialist_definition",
    "build_love_relational_dynamics_specialist_definition",
    "build_love_study_laboratory_descriptor",
    "build_love_study_prototype_definition",
]
