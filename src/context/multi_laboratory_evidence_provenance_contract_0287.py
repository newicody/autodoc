"""Immutable multi-laboratory evidence provenance for phase 0287-r3.

The contract binds each r2 evidence item to an existing laboratory visit and,
when needed, to the existing specialist transfer chain. It validates identity
and continuity only. Deduplication, contradiction detection, weighting,
durable history, Scheduler selection and observation remain later phases.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Literal

from context.laboratory_framework_contract_0273 import (
    LaboratoryVisitRequest,
    LaboratoryVisitResult,
    validate_laboratory_visit_result,
)
from context.multi_laboratory_evidence_aggregation_contract_0287 import (
    MultiLaboratoryEvidenceAggregate,
    MultiLaboratoryEvidenceItem,
)
from context.specialist_laboratory_transfer_contract_0284 import (
    SpecialistTransferRequest,
    SpecialistTransferResult,
    SpecialistTransferVisitPlan,
    validate_specialist_transfer_chain,
)

MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA = (
    "missipy.multi_laboratory.evidence_provenance.v1"
)
MULTI_LABORATORY_EVIDENCE_PROVENANCE_VALIDATION_SCHEMA = (
    "missipy.multi_laboratory.evidence_provenance_validation.v1"
)
MULTI_LABORATORY_EVIDENCE_PROVENANCE_CONTRACT_VERSION = "0287.r3"

MultiLaboratoryEvidenceVisitStatus = Literal[
    "completed", "failed", "needs_context", "needs_specialist", "rejected"
]

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PROVENANCE_PREFIXES = ("provenance:",)
_EVIDENCE_PREFIXES = (
    "artifact:", "evidence:", "observation:", "report:", "result:",
    "sql:", "test:", "validation:", "ctx:", "ctx-result:",
    "ctx-fragment:",
)
_LABORATORY_PREFIXES = ("laboratory:",)
_VISIT_PREFIXES = ("laboratory-visit:",)
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_SOURCE_PREFIXES = (
    "artifact:", "conversation:", "event:", "github:", "observation:",
    "report:", "result:", "sql:", "test:", "validation:", "ctx:",
    "ctx-result:", "ctx-fragment:",
)
_CONVERSATION_PREFIXES = ("laboratory-conversation:", "conversation:")
_TRANSFER_PREFIXES = ("specialist-transfer:",)
_ALLOWED_VISIT_STATUSES = frozenset(
    {"completed", "failed", "needs_context", "needs_specialist", "rejected"}
)


class MultiLaboratoryEvidenceProvenanceContractError(ValueError):
    """Raised when evidence provenance is malformed or inconsistent."""


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceProvenance:
    """One immutable evidence-to-laboratory provenance chain."""

    schema: str
    provenance_ref: str
    evidence_ref: str
    laboratory_ref: str
    visit_ref: str
    specialist_ref: str
    source_ref: str
    visit_status: MultiLaboratoryEvidenceVisitStatus
    origin_laboratory_ref: str
    target_laboratory_ref: str
    conversation_ref: str | None = None
    parent_visit_ref: str | None = None
    transfer_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA:
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "unsupported evidence provenance schema"
            )
        _require_ref("provenance_ref", self.provenance_ref, _PROVENANCE_PREFIXES)
        _require_ref("evidence_ref", self.evidence_ref, _EVIDENCE_PREFIXES)
        _require_ref("laboratory_ref", self.laboratory_ref, _LABORATORY_PREFIXES)
        _require_ref("visit_ref", self.visit_ref, _VISIT_PREFIXES)
        _require_ref("specialist_ref", self.specialist_ref, _SPECIALIST_PREFIXES)
        _require_ref("source_ref", self.source_ref, _SOURCE_PREFIXES)
        if self.visit_status not in _ALLOWED_VISIT_STATUSES:
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "unsupported visit_status"
            )
        _require_ref(
            "origin_laboratory_ref", self.origin_laboratory_ref,
            _LABORATORY_PREFIXES,
        )
        _require_ref(
            "target_laboratory_ref", self.target_laboratory_ref,
            _LABORATORY_PREFIXES,
        )
        if self.target_laboratory_ref != self.laboratory_ref:
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "target_laboratory_ref must equal laboratory_ref"
            )
        cross_laboratory = (
            self.origin_laboratory_ref != self.target_laboratory_ref
        )
        if self.conversation_ref is not None:
            _require_ref(
                "conversation_ref", self.conversation_ref,
                _CONVERSATION_PREFIXES,
            )
        if self.parent_visit_ref is not None:
            _require_ref("parent_visit_ref", self.parent_visit_ref, _VISIT_PREFIXES)
            if self.parent_visit_ref == self.visit_ref:
                raise MultiLaboratoryEvidenceProvenanceContractError(
                    "parent_visit_ref must differ from visit_ref"
                )
        if self.transfer_ref is not None:
            _require_ref("transfer_ref", self.transfer_ref, _TRANSFER_PREFIXES)
        if cross_laboratory and (
            self.conversation_ref is None
            or self.parent_visit_ref is None
            or self.transfer_ref is None
        ):
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "cross-laboratory provenance requires conversation, parent visit and transfer"
            )
        if not cross_laboratory and self.transfer_ref is not None:
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "same-laboratory provenance cannot carry transfer_ref"
            )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def cross_laboratory(self) -> bool:
        return self.origin_laboratory_ref != self.target_laboratory_ref

    @property
    def provenance_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_provenance_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(
        self, *, include_provenance_digest: bool = True
    ) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "provenance_ref": self.provenance_ref,
            "evidence_ref": self.evidence_ref,
            "laboratory_ref": self.laboratory_ref,
            "visit_ref": self.visit_ref,
            "specialist_ref": self.specialist_ref,
            "source_ref": self.source_ref,
            "visit_status": self.visit_status,
            "origin_laboratory_ref": self.origin_laboratory_ref,
            "target_laboratory_ref": self.target_laboratory_ref,
            "conversation_ref": self.conversation_ref,
            "parent_visit_ref": self.parent_visit_ref,
            "transfer_ref": self.transfer_ref,
            "cross_laboratory": self.cross_laboratory,
            "metadata": dict(self.metadata),
            "authoritative": False,
            "approved": False,
            "deduplication_performed": False,
            "contradiction_detection_performed": False,
            "weighting_authorized": False,
            "durable_state_written": False,
            "scheduler_selection_allowed": False,
        }
        if include_provenance_digest:
            mapping["provenance_digest"] = self.provenance_digest
        return mapping


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceProvenanceValidationResult:
    """Pure validation result for one r2 aggregate and its provenances."""

    schema: str
    valid: bool
    issues: tuple[str, ...]
    aggregation_ref: str
    aggregation_digest: str
    evidence_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    laboratory_refs: tuple[str, ...]
    visit_refs: tuple[str, ...]
    specialist_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    provenance_digests: tuple[str, ...]
    multi_laboratory_confirmed: bool
    transfer_continuity_validated: bool
    provenance_chain_validated: bool
    validation_digest: str
    authoritative: bool = field(default=False, init=False)
    approved: bool = field(default=False, init=False)
    deduplication_performed: bool = field(default=False, init=False)
    contradiction_detection_performed: bool = field(default=False, init=False)
    weighting_authorized: bool = field(default=False, init=False)
    durable_state_written: bool = field(default=False, init=False)
    scheduler_selection_allowed: bool = field(default=False, init=False)
    laboratory_self_authorization_allowed: bool = field(default=False, init=False)
    specialist_self_authorization_allowed: bool = field(default=False, init=False)
    sql_remains_durable_authority: bool = field(default=True, init=False)
    scheduler_remains_only_orchestrator: bool = field(default=True, init=False)
    qdrant_authoritative: bool = field(default=False, init=False)
    github_projects_authoritative: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_PROVENANCE_VALIDATION_SCHEMA:
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "unsupported provenance validation schema"
            )
        if self.valid != (
            not self.issues
            and self.multi_laboratory_confirmed
            and self.provenance_chain_validated
        ):
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "valid flag does not match provenance validation state"
            )
        if not _SHA256_RE.fullmatch(self.aggregation_digest):
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "aggregation_digest must be SHA-256"
            )
        if not _SHA256_RE.fullmatch(self.validation_digest):
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "validation_digest must be SHA-256"
            )
        object.__setattr__(self, "issues", tuple(self.issues))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "aggregation_ref": self.aggregation_ref,
            "aggregation_digest": self.aggregation_digest,
            "evidence_refs": list(self.evidence_refs),
            "provenance_refs": list(self.provenance_refs),
            "laboratory_refs": list(self.laboratory_refs),
            "visit_refs": list(self.visit_refs),
            "specialist_refs": list(self.specialist_refs),
            "source_refs": list(self.source_refs),
            "provenance_digests": list(self.provenance_digests),
            "multi_laboratory_confirmed": self.multi_laboratory_confirmed,
            "transfer_continuity_validated": self.transfer_continuity_validated,
            "provenance_chain_validated": self.provenance_chain_validated,
            "validation_digest": self.validation_digest,
            "authoritative": False,
            "approved": False,
            "deduplication_performed": False,
            "contradiction_detection_performed": False,
            "weighting_authorized": False,
            "durable_state_written": False,
            "scheduler_selection_allowed": False,
            "laboratory_self_authorization_allowed": False,
            "specialist_self_authorization_allowed": False,
            "sql_remains_durable_authority": True,
            "scheduler_remains_only_orchestrator": True,
            "qdrant_authoritative": False,
            "github_projects_authoritative": False,
        }


def multi_laboratory_evidence_provenance_from_visit(
    item: MultiLaboratoryEvidenceItem,
    request: LaboratoryVisitRequest,
    result: LaboratoryVisitResult,
    *,
    transfer_request: SpecialistTransferRequest | None = None,
    transfer_plan: SpecialistTransferVisitPlan | None = None,
    transfer_result: SpecialistTransferResult | None = None,
) -> MultiLaboratoryEvidenceProvenance:
    """Bind one r2 item to an existing visit and optional transfer chain."""

    if not isinstance(item, MultiLaboratoryEvidenceItem):
        raise TypeError("item must be MultiLaboratoryEvidenceItem")
    issues = list(validate_laboratory_visit_result(request, result))
    if result.status != "completed":
        issues.append("evidence provenance requires a completed visit")
    if item.evidence_ref not in result.evidence_refs:
        issues.append("evidence_ref must be present in the visit result")
    if item.specialist_ref != result.specialist_ref:
        issues.append("item specialist_ref must match the visit result")

    cross_laboratory = (
        request.origin_laboratory_ref != request.target_laboratory_ref
    )
    transfer_ref: str | None = None
    transfer_values = (transfer_request, transfer_plan, transfer_result)
    if cross_laboratory:
        if any(value is None for value in transfer_values):
            issues.append(
                "cross-laboratory visit requires the complete transfer chain"
            )
        else:
            assert transfer_request is not None
            assert transfer_plan is not None
            assert transfer_result is not None
            issues.extend(
                validate_specialist_transfer_chain(
                    transfer_request, transfer_plan, transfer_result
                )
            )
            transfer_ref = transfer_request.transfer_ref
            if transfer_plan.target_visit_ref != request.visit_ref:
                issues.append("transfer target visit must match visit request")
            if transfer_result.target_visit_ref != request.visit_ref:
                issues.append("transfer result target visit must match visit request")
            if transfer_result.target_laboratory_ref != request.laboratory_ref:
                issues.append("transfer target laboratory must match visit request")
            if transfer_result.status not in {"accepted", "completed"}:
                issues.append("transfer result must be accepted or completed")
            if item.evidence_ref not in transfer_result.evidence_refs:
                issues.append("evidence_ref must be present in transfer result")
    elif any(value is not None for value in transfer_values):
        issues.append("same-laboratory visit cannot carry a transfer chain")

    if issues:
        raise MultiLaboratoryEvidenceProvenanceContractError(
            "; ".join(dict.fromkeys(issues))
        )
    return MultiLaboratoryEvidenceProvenance(
        schema=MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA,
        provenance_ref=item.provenance_ref,
        evidence_ref=item.evidence_ref,
        laboratory_ref=request.laboratory_ref,
        visit_ref=request.visit_ref,
        specialist_ref=result.specialist_ref,
        source_ref=item.source_ref,
        visit_status=result.status,
        origin_laboratory_ref=request.origin_laboratory_ref,
        target_laboratory_ref=request.target_laboratory_ref,
        conversation_ref=request.conversation_ref,
        parent_visit_ref=request.parent_visit_ref,
        transfer_ref=transfer_ref,
        metadata=(("source_contract", result.output_contract_ref),),
    )


def validate_multi_laboratory_evidence_provenance(
    aggregate: MultiLaboratoryEvidenceAggregate,
    provenances: Sequence[MultiLaboratoryEvidenceProvenance],
) -> MultiLaboratoryEvidenceProvenanceValidationResult:
    """Validate exact evidence/provenance bindings for one r2 aggregate."""

    if not isinstance(aggregate, MultiLaboratoryEvidenceAggregate):
        raise TypeError("aggregate must be MultiLaboratoryEvidenceAggregate")
    values = tuple(provenances)
    issues: list[str] = []
    if not all(isinstance(value, MultiLaboratoryEvidenceProvenance) for value in values):
        raise TypeError("provenances must contain provenance contracts")
    refs = tuple(value.provenance_ref for value in values)
    if len(set(refs)) != len(refs):
        issues.append("provenance_ref values must be unique")
    evidence_refs = tuple(value.evidence_ref for value in values)
    if len(set(evidence_refs)) != len(evidence_refs):
        issues.append("each evidence_ref must have one provenance")

    by_ref = {value.provenance_ref: value for value in values}
    for item in aggregate.evidence_items:
        provenance = by_ref.get(item.provenance_ref)
        if provenance is None:
            issues.append(f"missing provenance: {item.provenance_ref}")
            continue
        if provenance.evidence_ref != item.evidence_ref:
            issues.append(f"evidence_ref mismatch: {item.evidence_ref}")
        if provenance.specialist_ref != item.specialist_ref:
            issues.append(f"specialist_ref mismatch: {item.evidence_ref}")
        if provenance.source_ref != item.source_ref:
            issues.append(f"source_ref mismatch: {item.evidence_ref}")
        if provenance.visit_status != "completed":
            issues.append(f"visit not completed: {item.evidence_ref}")
    expected_refs = set(aggregate.provenance_refs)
    extra_refs = set(by_ref) - expected_refs
    if extra_refs:
        issues.append("unexpected provenance refs: " + ", ".join(sorted(extra_refs)))

    laboratory_refs = tuple(sorted({value.laboratory_ref for value in values}))
    multi_laboratory_confirmed = len(laboratory_refs) >= 2
    if not multi_laboratory_confirmed:
        issues.append("at least two distinct laboratory_ref values are required")
    transfer_continuity_validated = all(
        not value.cross_laboratory or value.transfer_ref is not None
        for value in values
    )
    if not transfer_continuity_validated:
        issues.append("cross-laboratory transfer continuity is incomplete")

    issues = list(dict.fromkeys(issues))
    provenance_chain_validated = not issues
    digest = _validation_digest(aggregate, values, issues)
    return MultiLaboratoryEvidenceProvenanceValidationResult(
        schema=MULTI_LABORATORY_EVIDENCE_PROVENANCE_VALIDATION_SCHEMA,
        valid=not issues and multi_laboratory_confirmed,
        issues=tuple(issues),
        aggregation_ref=aggregate.aggregation_ref,
        aggregation_digest=aggregate.aggregation_digest,
        evidence_refs=tuple(sorted(evidence_refs)),
        provenance_refs=tuple(sorted(refs)),
        laboratory_refs=laboratory_refs,
        visit_refs=tuple(sorted({value.visit_ref for value in values})),
        specialist_refs=tuple(sorted({value.specialist_ref for value in values})),
        source_refs=tuple(sorted({value.source_ref for value in values})),
        provenance_digests=tuple(
            sorted(value.provenance_digest for value in values)
        ),
        multi_laboratory_confirmed=multi_laboratory_confirmed,
        transfer_continuity_validated=transfer_continuity_validated,
        provenance_chain_validated=provenance_chain_validated,
        validation_digest=digest,
    )


def _validation_digest(
    aggregate: MultiLaboratoryEvidenceAggregate,
    values: Sequence[MultiLaboratoryEvidenceProvenance],
    issues: Sequence[str],
) -> str:
    payload = {
        "schema": MULTI_LABORATORY_EVIDENCE_PROVENANCE_VALIDATION_SCHEMA,
        "aggregation_ref": aggregate.aggregation_ref,
        "aggregation_digest": aggregate.aggregation_digest,
        "provenance_digests": sorted(value.provenance_digest for value in values),
        "issues": list(issues),
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_ref(name: str, value: str, prefixes: tuple[str, ...]) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise MultiLaboratoryEvidenceProvenanceContractError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(prefixes):
        raise MultiLaboratoryEvidenceProvenanceContractError(
            f"{name} must start with one of: {', '.join(prefixes)}"
        )


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        if not isinstance(key, str) or not key.strip():
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "metadata key must be non-empty"
            )
        if not isinstance(value, str) or not value.strip():
            raise MultiLaboratoryEvidenceProvenanceContractError(
                "metadata value must be non-empty"
            )
        normalized[key.strip()] = value.strip()
    return tuple(sorted(normalized.items()))


__all__ = (
    "MULTI_LABORATORY_EVIDENCE_PROVENANCE_CONTRACT_VERSION",
    "MULTI_LABORATORY_EVIDENCE_PROVENANCE_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_PROVENANCE_VALIDATION_SCHEMA",
    "MultiLaboratoryEvidenceProvenance",
    "MultiLaboratoryEvidenceProvenanceContractError",
    "MultiLaboratoryEvidenceProvenanceValidationResult",
    "MultiLaboratoryEvidenceVisitStatus",
    "multi_laboratory_evidence_provenance_from_visit",
    "validate_multi_laboratory_evidence_provenance",
)
