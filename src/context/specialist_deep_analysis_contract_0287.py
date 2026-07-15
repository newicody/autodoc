"""Generic deep-analysis contracts for specialist work in phase 0287-r7-r8.

Specialists primarily return rich domain analyses.  A local or global synthesis
is possible only when the mission asks for that contribution kind.  The later
mutualized synthesis remains owned by the existing liaison boundary.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import re
from types import MappingProxyType
from typing import Any, Literal, Protocol

from context.specialist_laboratory_message_v2_0287 import (
    SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA,
    SpecialistArtifactReference,
    SpecialistLaboratoryMessageV2,
    compute_payload_sha256,
    stable_idempotency_key,
)

DEEP_ANALYSIS_REQUEST_SCHEMA = "missipy.specialist.deep_analysis_request.v1"
DEEP_ANALYSIS_FINDING_SCHEMA = "missipy.specialist.deep_analysis_finding.v1"
DEEP_ANALYSIS_CONTRIBUTION_SCHEMA = (
    "missipy.specialist.deep_analysis_contribution.v1"
)
DEEP_ANALYSIS_FRAGMENT_PROJECTION_SCHEMA = (
    "missipy.specialist.output_fragment_projection.v1"
)

DeepAnalysisDepth = Literal["focused", "deep", "exhaustive"]
DeepAnalysisContributionKind = Literal[
    "domain_analysis",
    "local_synthesis",
    "critique",
    "validation",
    "comparison",
    "recommendation",
    "global_synthesis",
]
DeepAnalysisFindingStatus = Literal["observed", "inferred", "unresolved"]

_ALLOWED_DEPTHS = frozenset({"focused", "deep", "exhaustive"})
_ALLOWED_CONTRIBUTION_KINDS = frozenset(
    {
        "domain_analysis",
        "local_synthesis",
        "critique",
        "validation",
        "comparison",
        "recommendation",
        "global_synthesis",
    }
)
_ALLOWED_FINDING_STATUS = frozenset({"observed", "inferred", "unresolved"})
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_ANALYSIS_REQUEST_PREFIXES = ("analysis-request:",)
_CONTRIBUTION_PREFIXES = ("specialist-contribution:",)
_FINDING_PREFIXES = ("finding:",)
_MISSION_PREFIXES = ("mission:",)
_DOMAIN_PREFIXES = ("domain:",)
_WORK_PACKAGE_PREFIXES = ("research-work-package:",)
_CONVERSATION_PREFIXES = ("laboratory-conversation:",)
_ROUTE_PREFIXES = ("route:", "specialist-path:")
_CONTRACT_PREFIXES = ("contract:",)
_VISIT_PREFIXES = ("laboratory-visit:",)
_CONTEXT_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "qdrant:",
    "artifact:",
    "dataset:",
    "research-work-package:",
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
_MAX_ITEMS = 1_024
_MAX_TEXT_CHARS = 1_000_000
_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))


class DeepAnalysisContractError(ValueError):
    """Raised when a deep-analysis contract is incoherent."""


class CorrelatedResearchWorkPackageLike(Protocol):
    work_package_ref: str
    conversation_ref: str
    return_route_ref: str
    context_refs: Sequence[str]
    evidence_refs: Sequence[str]
    attachments: Sequence[Any]
    authoritative_request: Mapping[str, Any]
    copilot_advisory: Mapping[str, Any]

    def to_mapping(self) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class DeepAnalysisFinding:
    """One evidence-linked finding inside a specialist contribution."""

    schema: str
    finding_ref: str
    status: DeepAnalysisFindingStatus
    statement: str
    confidence: float
    evidence_refs: tuple[str, ...]
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.schema != DEEP_ANALYSIS_FINDING_SCHEMA:
            raise DeepAnalysisContractError(
                "unsupported deep analysis finding schema"
            )
        _require_typed_ref("finding_ref", self.finding_ref, _FINDING_PREFIXES)
        if self.status not in _ALLOWED_FINDING_STATUS:
            raise DeepAnalysisContractError("unsupported finding status")
        _require_text("statement", self.statement)
        if isinstance(self.confidence, bool) or not isinstance(
            self.confidence, (int, float)
        ):
            raise DeepAnalysisContractError("confidence must be numeric")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise DeepAnalysisContractError("confidence must be between 0 and 1")
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs",
                self.evidence_refs,
                _EVIDENCE_PREFIXES,
                allow_empty=self.status == "unresolved",
            ),
        )
        if self.rationale:
            _require_text("rationale", self.rationale)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "finding_ref": self.finding_ref,
            "status": self.status,
            "statement": self.statement,
            "confidence": self.confidence,
            "evidence_refs": list(self.evidence_refs),
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class DeepAnalysisRequest:
    """Immutable mission asking one specialist for a bounded contribution."""

    schema: str
    request_ref: str
    mission_ref: str
    work_package_ref: str
    conversation_ref: str
    return_route_ref: str
    specialist_ref: str
    domain_ref: str
    objective: str
    input_contract_ref: str
    expected_output_contract_ref: str
    requested_contribution_kind: DeepAnalysisContributionKind
    depth: DeepAnalysisDepth
    constraints: tuple[str, ...]
    success_criteria: tuple[str, ...]
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    attachment_refs: tuple[str, ...] = ()
    advisory_ref: str | None = None

    def __post_init__(self) -> None:
        if self.schema != DEEP_ANALYSIS_REQUEST_SCHEMA:
            raise DeepAnalysisContractError(
                "unsupported deep analysis request schema"
            )
        _require_typed_ref("request_ref", self.request_ref, _ANALYSIS_REQUEST_PREFIXES)
        _require_typed_ref("mission_ref", self.mission_ref, _MISSION_PREFIXES)
        _require_typed_ref(
            "work_package_ref", self.work_package_ref, _WORK_PACKAGE_PREFIXES
        )
        _require_typed_ref(
            "conversation_ref", self.conversation_ref, _CONVERSATION_PREFIXES
        )
        _require_typed_ref("return_route_ref", self.return_route_ref, _ROUTE_PREFIXES)
        _require_typed_ref("specialist_ref", self.specialist_ref, _SPECIALIST_PREFIXES)
        _require_typed_ref("domain_ref", self.domain_ref, _DOMAIN_PREFIXES)
        _require_text("objective", self.objective)
        _require_typed_ref(
            "input_contract_ref", self.input_contract_ref, _CONTRACT_PREFIXES
        )
        _require_typed_ref(
            "expected_output_contract_ref",
            self.expected_output_contract_ref,
            _CONTRACT_PREFIXES,
        )
        if self.requested_contribution_kind not in _ALLOWED_CONTRIBUTION_KINDS:
            raise DeepAnalysisContractError("unsupported contribution kind")
        if self.depth not in _ALLOWED_DEPTHS:
            raise DeepAnalysisContractError("unsupported analysis depth")
        object.__setattr__(
            self,
            "constraints",
            _normalize_texts("constraints", self.constraints, allow_empty=True),
        )
        object.__setattr__(
            self,
            "success_criteria",
            _normalize_texts(
                "success_criteria", self.success_criteria, allow_empty=False
            ),
        )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs(
                "context_refs", self.context_refs, _CONTEXT_PREFIXES, allow_empty=True
            ),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs",
                self.evidence_refs,
                _EVIDENCE_PREFIXES,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "attachment_refs",
            _normalize_refs(
                "attachment_refs",
                self.attachment_refs,
                ("dataset:", "artifact:", "raw-dataset:"),
                allow_empty=True,
            ),
        )
        if self.advisory_ref is not None:
            _require_typed_ref(
                "advisory_ref", self.advisory_ref, ("github-advisory:", "artifact:")
            )

    @property
    def global_synthesis_requested(self) -> bool:
        return self.requested_contribution_kind == "global_synthesis"

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "request_ref": self.request_ref,
            "mission_ref": self.mission_ref,
            "work_package_ref": self.work_package_ref,
            "conversation_ref": self.conversation_ref,
            "return_route_ref": self.return_route_ref,
            "specialist_ref": self.specialist_ref,
            "domain_ref": self.domain_ref,
            "objective": self.objective,
            "input_contract_ref": self.input_contract_ref,
            "expected_output_contract_ref": self.expected_output_contract_ref,
            "requested_contribution_kind": self.requested_contribution_kind,
            "depth": self.depth,
            "constraints": list(self.constraints),
            "success_criteria": list(self.success_criteria),
            "context_refs": list(self.context_refs),
            "evidence_refs": list(self.evidence_refs),
            "attachment_refs": list(self.attachment_refs),
            "advisory_ref": self.advisory_ref,
            "request_authority": "operator-approved-work-package",
            "copilot_advisory_authoritative": False,
            "global_synthesis_requested": self.global_synthesis_requested,
            "scheduler_route_created": False,
        }


@dataclass(frozen=True, slots=True)
class DeepAnalysisContribution:
    """Rich specialist contribution prepared for later liaison synthesis."""

    schema: str
    contribution_ref: str
    request_ref: str
    specialist_ref: str
    visit_ref: str
    domain_ref: str
    contribution_kind: DeepAnalysisContributionKind
    output_contract_ref: str
    findings: tuple[DeepAnalysisFinding, ...]
    human_representation: str
    machine_payload: Mapping[str, Any] = field(default_factory=dict)
    uncertainties: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    requested_context_refs: tuple[str, ...] = ()
    requested_specialist_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    artifact_refs: tuple[SpecialistArtifactReference, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != DEEP_ANALYSIS_CONTRIBUTION_SCHEMA:
            raise DeepAnalysisContractError(
                "unsupported deep analysis contribution schema"
            )
        _require_typed_ref(
            "contribution_ref", self.contribution_ref, _CONTRIBUTION_PREFIXES
        )
        _require_typed_ref("request_ref", self.request_ref, _ANALYSIS_REQUEST_PREFIXES)
        _require_typed_ref("specialist_ref", self.specialist_ref, _SPECIALIST_PREFIXES)
        _require_typed_ref("visit_ref", self.visit_ref, _VISIT_PREFIXES)
        _require_typed_ref("domain_ref", self.domain_ref, _DOMAIN_PREFIXES)
        if self.contribution_kind not in _ALLOWED_CONTRIBUTION_KINDS:
            raise DeepAnalysisContractError("unsupported contribution kind")
        _require_typed_ref(
            "output_contract_ref", self.output_contract_ref, _CONTRACT_PREFIXES
        )
        findings = tuple(self.findings)
        if not findings or not all(
            isinstance(item, DeepAnalysisFinding) for item in findings
        ):
            raise DeepAnalysisContractError(
                "findings must contain at least one DeepAnalysisFinding"
            )
        finding_refs = tuple(item.finding_ref for item in findings)
        if len(set(finding_refs)) != len(finding_refs):
            raise DeepAnalysisContractError("finding_ref values must be unique")
        object.__setattr__(self, "findings", findings)
        _require_text("human_representation", self.human_representation)
        if not isinstance(self.machine_payload, Mapping):
            raise DeepAnalysisContractError("machine_payload must be a mapping")
        object.__setattr__(
            self,
            "machine_payload",
            _freeze_json_mapping(self.machine_payload),
        )
        for name in (
            "uncertainties",
            "contradictions",
            "limitations",
            "recommendations",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_texts(name, getattr(self, name), allow_empty=True),
            )
        object.__setattr__(
            self,
            "requested_context_refs",
            _normalize_refs(
                "requested_context_refs",
                self.requested_context_refs,
                _CONTEXT_PREFIXES,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "requested_specialist_refs",
            _normalize_refs(
                "requested_specialist_refs",
                self.requested_specialist_refs,
                _SPECIALIST_PREFIXES,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs",
                self.evidence_refs,
                _EVIDENCE_PREFIXES,
                allow_empty=True,
            ),
        )
        artifacts = tuple(self.artifact_refs)
        if not all(isinstance(item, SpecialistArtifactReference) for item in artifacts):
            raise DeepAnalysisContractError(
                "artifact_refs must contain SpecialistArtifactReference values"
            )
        object.__setattr__(self, "artifact_refs", artifacts)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "contribution_ref": self.contribution_ref,
            "request_ref": self.request_ref,
            "specialist_ref": self.specialist_ref,
            "visit_ref": self.visit_ref,
            "domain_ref": self.domain_ref,
            "contribution_kind": self.contribution_kind,
            "output_contract_ref": self.output_contract_ref,
            "findings": [item.to_mapping() for item in self.findings],
            "human_representation": self.human_representation,
            "machine_payload": _thaw_json(self.machine_payload),
            "uncertainties": list(self.uncertainties),
            "contradictions": list(self.contradictions),
            "limitations": list(self.limitations),
            "recommendations": list(self.recommendations),
            "requested_context_refs": list(self.requested_context_refs),
            "requested_specialist_refs": list(self.requested_specialist_refs),
            "evidence_refs": list(self.evidence_refs),
            "artifact_refs": [item.to_mapping() for item in self.artifact_refs],
            "analysis_preserved_for_later_synthesis": True,
            "global_synthesis_performed": self.contribution_kind
            == "global_synthesis",
            "scheduler_command_emitted": False,
            "durable_write_performed": False,
        }


def build_deep_analysis_request_from_work_package(
    work_package: CorrelatedResearchWorkPackageLike,
    *,
    specialist_ref: str,
    domain_ref: str,
    objective: str,
    expected_output_contract_ref: str,
    contribution_kind: DeepAnalysisContributionKind = "domain_analysis",
    depth: DeepAnalysisDepth = "deep",
    constraints: Sequence[str] = (),
    success_criteria: Sequence[str],
    mission_ref: str,
    request_ref: str | None = None,
) -> DeepAnalysisRequest:
    """Project one validated research package into a specialist mission."""

    for name in ("work_package_ref", "conversation_ref", "return_route_ref"):
        if not hasattr(work_package, name):
            raise DeepAnalysisContractError(
                f"work package is missing required field: {name}"
            )
    package_mapping = dict(work_package.to_mapping())
    expected_boundaries = {
        "schema": "missipy.research.correlated_work_package.v1",
        "request_authoritative": True,
        "advisory_used_as_hint_only": True,
        "ready_for_laboratory_route": True,
        "scheduler_route_created": False,
    }
    for key, expected in expected_boundaries.items():
        if package_mapping.get(key) != expected:
            raise DeepAnalysisContractError(
                f"work package boundary mismatch: {key}"
            )
    attachment_refs = tuple(
        str(getattr(item, "raw_dataset_ref", ""))
        for item in work_package.attachments
    )
    if any(not item for item in attachment_refs):
        raise DeepAnalysisContractError(
            "work package attachments must expose raw_dataset_ref"
        )
    resolved_request_ref = request_ref or _stable_request_ref(
        work_package.work_package_ref,
        mission_ref,
        specialist_ref,
        domain_ref,
    )
    advisory = dict(work_package.copilot_advisory)
    advisory_ref = str(advisory.get("artifact_ref", "")).strip() or None
    return DeepAnalysisRequest(
        schema=DEEP_ANALYSIS_REQUEST_SCHEMA,
        request_ref=resolved_request_ref,
        mission_ref=mission_ref,
        work_package_ref=work_package.work_package_ref,
        conversation_ref=work_package.conversation_ref,
        return_route_ref=work_package.return_route_ref,
        specialist_ref=specialist_ref,
        domain_ref=domain_ref,
        objective=objective,
        input_contract_ref="contract:missipy.research.correlated_work_package.v1",
        expected_output_contract_ref=expected_output_contract_ref,
        requested_contribution_kind=contribution_kind,
        depth=depth,
        constraints=tuple(constraints),
        success_criteria=tuple(success_criteria),
        context_refs=tuple(work_package.context_refs)
        + (work_package.work_package_ref,),
        evidence_refs=tuple(work_package.evidence_refs),
        attachment_refs=attachment_refs,
        advisory_ref=advisory_ref,
    )


def build_deep_analysis_demand_message_v2(
    request: DeepAnalysisRequest,
    *,
    message_ref: str,
    visit_ref: str,
    laboratory_ref: str,
    correlation_ref: str,
    sequence_no: int = 0,
    parent_visit_ref: str | None = None,
    continuation_of_message_ref: str | None = None,
    reply_to_message_ref: str | None = None,
) -> SpecialistLaboratoryMessageV2:
    """Wrap a deep-analysis mission in the canonical v2 exchange message."""

    payload = request.to_mapping()
    return SpecialistLaboratoryMessageV2(
        schema=SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA,
        message_ref=message_ref,
        conversation_ref=request.conversation_ref,
        visit_ref=visit_ref,
        sequence_no=sequence_no,
        kind="demand",
        specialist_ref=request.specialist_ref,
        origin_laboratory_ref=laboratory_ref,
        target_laboratory_ref=laboratory_ref,
        sender_ref=laboratory_ref,
        recipient_ref=request.specialist_ref,
        payload_contract_ref=request.input_contract_ref,
        return_route_ref=request.return_route_ref,
        correlation_ref=correlation_ref,
        idempotency_key=stable_idempotency_key(
            correlation_ref,
            request.request_ref,
            visit_ref,
            "demand",
        ),
        human_representation=request.objective,
        payload=payload,
        payload_sha256=compute_payload_sha256(payload),
        reply_to_message_ref=reply_to_message_ref,
        parent_visit_ref=parent_visit_ref,
        continuation_of_message_ref=continuation_of_message_ref,
        context_refs=request.context_refs,
        evidence_refs=request.evidence_refs,
    )


def build_deep_analysis_contribution_message_v2(
    contribution: DeepAnalysisContribution,
    *,
    demand_message: SpecialistLaboratoryMessageV2,
    message_ref: str,
    sequence_no: int,
) -> SpecialistLaboratoryMessageV2:
    """Wrap one rich contribution without performing global synthesis."""

    if contribution.request_ref != str(
        demand_message.payload.get("request_ref", "")
    ):
        raise DeepAnalysisContractError(
            "contribution request_ref must match demand payload"
        )
    if contribution.specialist_ref != demand_message.specialist_ref:
        raise DeepAnalysisContractError(
            "contribution specialist_ref must match demand specialist"
        )
    payload = contribution.to_mapping()
    return SpecialistLaboratoryMessageV2(
        schema=SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA,
        message_ref=message_ref,
        conversation_ref=demand_message.conversation_ref,
        visit_ref=contribution.visit_ref,
        sequence_no=sequence_no,
        kind="analysis",
        specialist_ref=contribution.specialist_ref,
        origin_laboratory_ref=demand_message.origin_laboratory_ref,
        target_laboratory_ref=demand_message.target_laboratory_ref,
        sender_ref=contribution.specialist_ref,
        recipient_ref=demand_message.target_laboratory_ref,
        payload_contract_ref=contribution.output_contract_ref,
        return_route_ref=demand_message.return_route_ref,
        correlation_ref=demand_message.correlation_ref,
        idempotency_key=stable_idempotency_key(
            demand_message.correlation_ref,
            contribution.contribution_ref,
            "analysis",
        ),
        human_representation=contribution.human_representation,
        payload=payload,
        payload_sha256=compute_payload_sha256(payload),
        reply_to_message_ref=demand_message.message_ref,
        context_refs=contribution.requested_context_refs,
        evidence_refs=contribution.evidence_refs,
        artifact_refs=contribution.artifact_refs,
    )


def validate_contribution_for_request(
    request: DeepAnalysisRequest,
    contribution: DeepAnalysisContribution,
) -> tuple[str, ...]:
    """Return semantic mismatches without changing either contract."""

    issues: list[str] = []
    if contribution.request_ref != request.request_ref:
        issues.append("contribution request_ref does not match request")
    if contribution.specialist_ref != request.specialist_ref:
        issues.append("contribution specialist_ref does not match request")
    if contribution.domain_ref != request.domain_ref:
        issues.append("contribution domain_ref does not match request")
    if contribution.output_contract_ref != request.expected_output_contract_ref:
        issues.append("contribution output contract does not match request")
    if contribution.contribution_kind != request.requested_contribution_kind:
        issues.append("contribution kind does not match requested contribution kind")
    return tuple(issues)


def project_deep_analysis_to_output_fragment(
    contribution: DeepAnalysisContribution,
) -> dict[str, object]:
    """Build a deterministic mapping for the existing liaison boundary.

    The function deliberately returns a mapping rather than importing or
    replacing ``SpecialistOutputFragment``.  The later integration phase owns
    the exact constructor adapter after the real specialists exist.
    """

    return {
        "schema": DEEP_ANALYSIS_FRAGMENT_PROJECTION_SCHEMA,
        "fragment_ref": f"fragment:{contribution.contribution_ref.split(':', 1)[1]}",
        "specialist_ref": contribution.specialist_ref,
        "source_visit_ref": contribution.visit_ref,
        "output_contract_ref": contribution.output_contract_ref,
        "contribution_kind": contribution.contribution_kind,
        "machine_result": contribution.to_mapping(),
        "human_representation": contribution.human_representation,
        "evidence_refs": list(contribution.evidence_refs),
        "artifact_refs": [item.artifact_ref for item in contribution.artifact_refs],
        "uncertainties": list(contribution.uncertainties),
        "contradictions": list(contribution.contradictions),
        "limitations": list(contribution.limitations),
        "recommendations": list(contribution.recommendations),
        "ready_for_liaison_synthesis": True,
        "global_synthesis_performed": contribution.contribution_kind
        == "global_synthesis",
        "liaison_synthesis_created": False,
    }


def _stable_request_ref(*parts: str) -> str:
    for part in parts:
        _require_text("request seed", part)
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"analysis-request:{digest}"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DeepAnalysisContractError(f"{name} must be non-empty")
    if len(value) > _MAX_TEXT_CHARS:
        raise DeepAnalysisContractError(
            f"{name} exceeds {_MAX_TEXT_CHARS} characters"
        )


def _require_typed_ref(
    name: str,
    value: str,
    prefixes: tuple[str, ...],
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise DeepAnalysisContractError(f"{name} must be a typed reference")
    if not value.startswith(prefixes):
        raise DeepAnalysisContractError(
            f"{name} must start with one of: {', '.join(prefixes)}"
        )


def _normalize_texts(
    name: str,
    values: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise DeepAnalysisContractError(f"{name} must be a sequence of texts")
    normalized: list[str] = []
    for value in values:
        _require_text(name, value)
        normalized.append(value.strip())
    result = tuple(dict.fromkeys(normalized))
    if not result and not allow_empty:
        raise DeepAnalysisContractError(f"{name} must not be empty")
    if len(result) > _MAX_ITEMS:
        raise DeepAnalysisContractError(f"{name} exceeds {_MAX_ITEMS} values")
    return result


def _normalize_refs(
    name: str,
    refs: Sequence[str],
    prefixes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(refs, (str, bytes)):
        raise DeepAnalysisContractError(f"{name} must be a sequence of references")
    values = tuple(dict.fromkeys(refs))
    if not values and not allow_empty:
        raise DeepAnalysisContractError(f"{name} must not be empty")
    if len(values) > _MAX_ITEMS:
        raise DeepAnalysisContractError(f"{name} exceeds {_MAX_ITEMS} values")
    for value in values:
        _require_typed_ref(name, value, prefixes)
    return values


def _freeze_json_mapping(values: Mapping[str, Any]) -> Mapping[str, Any]:
    frozen: dict[str, Any] = {}
    for key, value in values.items():
        _require_text("machine_payload key", key)
        frozen[key] = _freeze_json(value)
    return MappingProxyType(frozen)


def _freeze_json(value: Any) -> Any:
    if isinstance(value, _JSON_SCALAR_TYPES):
        return value
    if isinstance(value, Mapping):
        return _freeze_json_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    raise DeepAnalysisContractError(
        f"machine_payload contains non-JSON value: {type(value).__name__}"
    )


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


__all__ = (
    "DEEP_ANALYSIS_CONTRIBUTION_SCHEMA",
    "DEEP_ANALYSIS_FINDING_SCHEMA",
    "DEEP_ANALYSIS_FRAGMENT_PROJECTION_SCHEMA",
    "DEEP_ANALYSIS_REQUEST_SCHEMA",
    "CorrelatedResearchWorkPackageLike",
    "DeepAnalysisContribution",
    "DeepAnalysisContributionKind",
    "DeepAnalysisContractError",
    "DeepAnalysisDepth",
    "DeepAnalysisFinding",
    "DeepAnalysisFindingStatus",
    "DeepAnalysisRequest",
    "build_deep_analysis_contribution_message_v2",
    "build_deep_analysis_demand_message_v2",
    "build_deep_analysis_request_from_work_package",
    "project_deep_analysis_to_output_fragment",
    "validate_contribution_for_request",
)
