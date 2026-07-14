"""Immutable specialist transfer contracts for phase 0284-r4.

The contracts describe a temporary visit or a durable transfer between two
laboratories while preserving the portable specialist identity and the existing
laboratory visit lineage.  They are pure plans/results: no transport, provider,
registry, Scheduler mutation, EventBus command, SQL/Qdrant effect, OpenVINO call
or GitHub mutation is performed here.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import hashlib
import re
from typing import Literal, Protocol

from context.portable_specialist_contract_0284 import (
    PortableSpecialistDescriptor,
    validate_portable_specialist_visit_contract,
)
from context.specialist_laboratory_message_contract_0284 import (
    SpecialistLaboratoryConversation,
)

SPECIALIST_LABORATORY_TRANSFER_CONTRACT_VERSION = "0284.r4"
SPECIALIST_TRANSFER_REQUEST_SCHEMA = "missipy.specialist.transfer_request.v1"
SPECIALIST_TRANSFER_VISIT_PLAN_SCHEMA = "missipy.specialist.transfer_visit_plan.v1"
SPECIALIST_TRANSFER_RESULT_SCHEMA = "missipy.specialist.transfer_result.v1"

SpecialistTransferMode = Literal["visit", "transfer"]
SpecialistTransferStatus = Literal["accepted", "rejected", "completed"]

_ALLOWED_TRANSFER_MODES = frozenset({"visit", "transfer"})
_ALLOWED_TRANSFER_STATUSES = frozenset({"accepted", "rejected", "completed"})
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_TRANSFER_PREFIXES = ("specialist-transfer:",)
_VISIT_PREFIXES = ("laboratory-visit:",)
_MESSAGE_PREFIXES = ("laboratory-message:",)
_CONVERSATION_PREFIXES = ("laboratory-conversation:",)
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_LABORATORY_PREFIXES = ("laboratory:",)
_CONTRACT_PREFIXES = ("contract:",)
_ROUTE_PREFIXES = ("route:", "specialist-path:")
_CONTEXT_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "qdrant:",
    "artifact:",
)
_EVIDENCE_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "artifact:",
    "validation:",
)
_MAX_REFS = 1_024
_MAX_TEXT_CHARS = 1_000_000


class SpecialistLaboratoryTransferContractError(ValueError):
    """Raised when a specialist transfer contract is incoherent."""


class LaboratoryTransferSourceRequestLike(Protocol):
    visit_ref: str
    laboratory_ref: str
    specialist_ref: str
    input_contract_ref: str
    expected_output_contract_ref: str
    return_route_ref: str
    context_refs: Sequence[str]
    evidence_refs: Sequence[str]
    origin_laboratory_ref: str | None
    target_laboratory_ref: str | None
    conversation_ref: str | None


class LaboratoryTransferSourceResultLike(Protocol):
    visit_ref: str
    laboratory_ref: str
    specialist_ref: str
    status: str
    output_contract_ref: str
    evidence_refs: Sequence[str]
    requested_context_refs: Sequence[str]
    requested_laboratory_refs: Sequence[str]
    conversation_ref: str | None


@dataclass(frozen=True, slots=True)
class SpecialistTransferRequest:
    """One immutable request for a temporary visit or durable transfer."""

    schema: str
    transfer_ref: str
    mode: SpecialistTransferMode
    specialist_ref: str
    conversation_ref: str
    source_visit_ref: str
    requested_by_message_ref: str
    origin_laboratory_ref: str
    target_laboratory_ref: str
    input_contract_ref: str
    expected_output_contract_ref: str
    return_route_ref: str
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    parent_transfer_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_TRANSFER_REQUEST_SCHEMA:
            raise SpecialistLaboratoryTransferContractError(
                "unsupported specialist transfer request schema"
            )
        _require_typed_ref("transfer_ref", self.transfer_ref, _TRANSFER_PREFIXES)
        if self.mode not in _ALLOWED_TRANSFER_MODES:
            raise SpecialistLaboratoryTransferContractError(
                "unsupported specialist transfer mode"
            )
        _require_typed_ref("specialist_ref", self.specialist_ref, _SPECIALIST_PREFIXES)
        _require_typed_ref(
            "conversation_ref", self.conversation_ref, _CONVERSATION_PREFIXES
        )
        _require_typed_ref("source_visit_ref", self.source_visit_ref, _VISIT_PREFIXES)
        _require_typed_ref(
            "requested_by_message_ref",
            self.requested_by_message_ref,
            _MESSAGE_PREFIXES,
        )
        _require_typed_ref(
            "origin_laboratory_ref", self.origin_laboratory_ref, _LABORATORY_PREFIXES
        )
        _require_typed_ref(
            "target_laboratory_ref", self.target_laboratory_ref, _LABORATORY_PREFIXES
        )
        if self.origin_laboratory_ref == self.target_laboratory_ref:
            raise SpecialistLaboratoryTransferContractError(
                "transfer origin and target laboratories must differ"
            )
        _require_typed_ref(
            "input_contract_ref", self.input_contract_ref, _CONTRACT_PREFIXES
        )
        _require_typed_ref(
            "expected_output_contract_ref",
            self.expected_output_contract_ref,
            _CONTRACT_PREFIXES,
        )
        _require_typed_ref("return_route_ref", self.return_route_ref, _ROUTE_PREFIXES)
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs("context_refs", self.context_refs, _CONTEXT_PREFIXES),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs("evidence_refs", self.evidence_refs, _EVIDENCE_PREFIXES),
        )
        if self.parent_transfer_ref is not None:
            _require_typed_ref(
                "parent_transfer_ref", self.parent_transfer_ref, _TRANSFER_PREFIXES
            )
            if self.parent_transfer_ref == self.transfer_ref:
                raise SpecialistLaboratoryTransferContractError(
                    "parent_transfer_ref must not equal transfer_ref"
                )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def portable_visit_mode(self) -> Literal["visitor", "transfer"]:
        return "visitor" if self.mode == "visit" else "transfer"

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "transfer_ref": self.transfer_ref,
            "mode": self.mode,
            "portable_visit_mode": self.portable_visit_mode,
            "specialist_ref": self.specialist_ref,
            "conversation_ref": self.conversation_ref,
            "source_visit_ref": self.source_visit_ref,
            "requested_by_message_ref": self.requested_by_message_ref,
            "origin_laboratory_ref": self.origin_laboratory_ref,
            "target_laboratory_ref": self.target_laboratory_ref,
            "input_contract_ref": self.input_contract_ref,
            "expected_output_contract_ref": self.expected_output_contract_ref,
            "return_route_ref": self.return_route_ref,
            "context_refs": list(self.context_refs),
            "evidence_refs": list(self.evidence_refs),
            "parent_transfer_ref": self.parent_transfer_ref,
            "metadata": dict(self.metadata),
            "specialist_identity_preserved": True,
            "scheduler_authorization_required": True,
            "transport_created": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistTransferVisitPlan:
    """Pure field plan for the next existing LaboratoryVisitRequest."""

    schema: str
    transfer_ref: str
    target_visit_ref: str
    specialist_ref: str
    laboratory_ref: str
    origin_laboratory_ref: str
    target_laboratory_ref: str
    conversation_ref: str
    parent_visit_ref: str
    input_contract_ref: str
    expected_output_contract_ref: str
    return_route_ref: str
    visit_mode: Literal["visitor", "transfer"]
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_TRANSFER_VISIT_PLAN_SCHEMA:
            raise SpecialistLaboratoryTransferContractError(
                "unsupported specialist transfer visit plan schema"
            )
        _require_typed_ref("transfer_ref", self.transfer_ref, _TRANSFER_PREFIXES)
        _require_typed_ref("target_visit_ref", self.target_visit_ref, _VISIT_PREFIXES)
        _require_typed_ref("specialist_ref", self.specialist_ref, _SPECIALIST_PREFIXES)
        _require_typed_ref("laboratory_ref", self.laboratory_ref, _LABORATORY_PREFIXES)
        _require_typed_ref(
            "origin_laboratory_ref", self.origin_laboratory_ref, _LABORATORY_PREFIXES
        )
        _require_typed_ref(
            "target_laboratory_ref", self.target_laboratory_ref, _LABORATORY_PREFIXES
        )
        if self.laboratory_ref != self.target_laboratory_ref:
            raise SpecialistLaboratoryTransferContractError(
                "visit plan laboratory_ref must equal target_laboratory_ref"
            )
        if self.origin_laboratory_ref == self.target_laboratory_ref:
            raise SpecialistLaboratoryTransferContractError(
                "visit plan origin and target laboratories must differ"
            )
        _require_typed_ref(
            "conversation_ref", self.conversation_ref, _CONVERSATION_PREFIXES
        )
        _require_typed_ref("parent_visit_ref", self.parent_visit_ref, _VISIT_PREFIXES)
        if self.parent_visit_ref == self.target_visit_ref:
            raise SpecialistLaboratoryTransferContractError(
                "target_visit_ref must differ from parent_visit_ref"
            )
        _require_typed_ref(
            "input_contract_ref", self.input_contract_ref, _CONTRACT_PREFIXES
        )
        _require_typed_ref(
            "expected_output_contract_ref",
            self.expected_output_contract_ref,
            _CONTRACT_PREFIXES,
        )
        _require_typed_ref("return_route_ref", self.return_route_ref, _ROUTE_PREFIXES)
        if self.visit_mode not in {"visitor", "transfer"}:
            raise SpecialistLaboratoryTransferContractError(
                "visit_mode must be visitor or transfer"
            )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs("context_refs", self.context_refs, _CONTEXT_PREFIXES),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs("evidence_refs", self.evidence_refs, _EVIDENCE_PREFIXES),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "transfer_ref": self.transfer_ref,
            "visit_mode": self.visit_mode,
            "laboratory_visit_request_fields": {
                "visit_ref": self.target_visit_ref,
                "laboratory_ref": self.laboratory_ref,
                "specialist_ref": self.specialist_ref,
                "input_contract_ref": self.input_contract_ref,
                "expected_output_contract_ref": self.expected_output_contract_ref,
                "return_route_ref": self.return_route_ref,
                "context_refs": list(self.context_refs),
                "evidence_refs": list(self.evidence_refs),
                "origin_laboratory_ref": self.origin_laboratory_ref,
                "target_laboratory_ref": self.target_laboratory_ref,
                "conversation_ref": self.conversation_ref,
                "parent_visit_ref": self.parent_visit_ref,
            },
            "scheduler_emit_required": True,
            "direct_provider_call_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistTransferResult:
    """Immutable outcome of an authorized specialist visit or transfer."""

    schema: str
    transfer_ref: str
    mode: SpecialistTransferMode
    status: SpecialistTransferStatus
    specialist_ref: str
    conversation_ref: str
    source_visit_ref: str
    target_visit_ref: str
    origin_laboratory_ref: str
    target_laboratory_ref: str
    active_laboratory_ref: str
    return_route_ref: str
    reason: str
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_TRANSFER_RESULT_SCHEMA:
            raise SpecialistLaboratoryTransferContractError(
                "unsupported specialist transfer result schema"
            )
        _require_typed_ref("transfer_ref", self.transfer_ref, _TRANSFER_PREFIXES)
        if self.mode not in _ALLOWED_TRANSFER_MODES:
            raise SpecialistLaboratoryTransferContractError(
                "unsupported specialist transfer mode"
            )
        if self.status not in _ALLOWED_TRANSFER_STATUSES:
            raise SpecialistLaboratoryTransferContractError(
                "unsupported specialist transfer status"
            )
        _require_typed_ref("specialist_ref", self.specialist_ref, _SPECIALIST_PREFIXES)
        _require_typed_ref(
            "conversation_ref", self.conversation_ref, _CONVERSATION_PREFIXES
        )
        _require_typed_ref("source_visit_ref", self.source_visit_ref, _VISIT_PREFIXES)
        _require_typed_ref("target_visit_ref", self.target_visit_ref, _VISIT_PREFIXES)
        _require_typed_ref(
            "origin_laboratory_ref", self.origin_laboratory_ref, _LABORATORY_PREFIXES
        )
        _require_typed_ref(
            "target_laboratory_ref", self.target_laboratory_ref, _LABORATORY_PREFIXES
        )
        _require_typed_ref(
            "active_laboratory_ref", self.active_laboratory_ref, _LABORATORY_PREFIXES
        )
        _require_typed_ref("return_route_ref", self.return_route_ref, _ROUTE_PREFIXES)
        _require_text("reason", self.reason)
        expected_active = _expected_active_laboratory(
            mode=self.mode,
            status=self.status,
            origin=self.origin_laboratory_ref,
            target=self.target_laboratory_ref,
        )
        if self.active_laboratory_ref != expected_active:
            raise SpecialistLaboratoryTransferContractError(
                "active_laboratory_ref is inconsistent with mode and status"
            )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs("context_refs", self.context_refs, _CONTEXT_PREFIXES),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs("evidence_refs", self.evidence_refs, _EVIDENCE_PREFIXES),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "transfer_ref": self.transfer_ref,
            "mode": self.mode,
            "status": self.status,
            "specialist_ref": self.specialist_ref,
            "conversation_ref": self.conversation_ref,
            "source_visit_ref": self.source_visit_ref,
            "target_visit_ref": self.target_visit_ref,
            "origin_laboratory_ref": self.origin_laboratory_ref,
            "target_laboratory_ref": self.target_laboratory_ref,
            "active_laboratory_ref": self.active_laboratory_ref,
            "return_route_ref": self.return_route_ref,
            "reason": self.reason,
            "context_refs": list(self.context_refs),
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
            "specialist_identity_preserved": True,
            "transport_created": False,
            "scheduler_remains_orchestrator": True,
        }


def build_specialist_transfer_request(
    descriptor: PortableSpecialistDescriptor,
    source_request: LaboratoryTransferSourceRequestLike,
    source_result: LaboratoryTransferSourceResultLike,
    conversation: SpecialistLaboratoryConversation,
    *,
    target_laboratory_ref: str,
    mode: SpecialistTransferMode,
    requested_by_message_ref: str | None = None,
    transfer_ref: str | None = None,
) -> SpecialistTransferRequest:
    """Build a transfer request from an existing visit result and conversation."""

    issues = _validate_source_links(source_request, source_result, conversation)
    if target_laboratory_ref not in tuple(source_result.requested_laboratory_refs):
        issues.append("target laboratory was not requested by source visit result")
    portable_mode = "visitor" if mode == "visit" else "transfer"
    issues.extend(
        validate_portable_specialist_visit_contract(
            descriptor,
            specialist_ref=source_request.specialist_ref,
            laboratory_ref=target_laboratory_ref,
            input_contract_ref=source_request.input_contract_ref,
            output_contract_ref=source_request.expected_output_contract_ref,
            visit_mode=portable_mode,
        )
    )
    if source_result.status in {"rejected", "failed", "cancelled"}:
        issues.append("failed source visit cannot request a specialist transfer")
    chosen_message_ref = requested_by_message_ref or conversation.messages[-1].message_ref
    message_by_ref = {item.message_ref: item for item in conversation.messages}
    chosen_message = message_by_ref.get(chosen_message_ref)
    if chosen_message is None:
        issues.append("requested_by_message_ref is not part of conversation")
    elif chosen_message.kind not in {
        "opinion",
        "specialist_request",
        "laboratory_request",
        "result",
    }:
        issues.append("requested_by_message_ref cannot open a transfer")
    elif (
        "target_laboratory_ref" in chosen_message.payload
        and chosen_message.payload["target_laboratory_ref"] != target_laboratory_ref
    ):
        issues.append("message target_laboratory_ref must match transfer target")
    if source_result.output_contract_ref not in descriptor.produced_output_contract_refs:
        issues.append("source result output contract is not produced by specialist")
    if issues:
        raise SpecialistLaboratoryTransferContractError("; ".join(dict.fromkeys(issues)))
    origin = source_request.laboratory_ref
    resolved_transfer_ref = transfer_ref or _stable_transfer_ref(
        source_request.visit_ref,
        target_laboratory_ref,
        mode,
    )
    return SpecialistTransferRequest(
        schema=SPECIALIST_TRANSFER_REQUEST_SCHEMA,
        transfer_ref=resolved_transfer_ref,
        mode=mode,
        specialist_ref=source_request.specialist_ref,
        conversation_ref=conversation.conversation_ref,
        source_visit_ref=source_request.visit_ref,
        requested_by_message_ref=chosen_message_ref,
        origin_laboratory_ref=origin,
        target_laboratory_ref=target_laboratory_ref,
        input_contract_ref=source_request.input_contract_ref,
        expected_output_contract_ref=source_request.expected_output_contract_ref,
        return_route_ref=source_request.return_route_ref,
        context_refs=_merge_refs(
            source_request.context_refs,
            source_result.requested_context_refs,
        ),
        evidence_refs=_merge_refs(
            source_request.evidence_refs,
            source_result.evidence_refs,
        ),
        metadata=(("source_result_status", source_result.status),),
    )


def build_specialist_transfer_visit_plan(
    request: SpecialistTransferRequest,
    *,
    target_visit_ref: str,
) -> SpecialistTransferVisitPlan:
    """Project a transfer request into fields for the existing visit contract."""

    return SpecialistTransferVisitPlan(
        schema=SPECIALIST_TRANSFER_VISIT_PLAN_SCHEMA,
        transfer_ref=request.transfer_ref,
        target_visit_ref=target_visit_ref,
        specialist_ref=request.specialist_ref,
        laboratory_ref=request.target_laboratory_ref,
        origin_laboratory_ref=request.origin_laboratory_ref,
        target_laboratory_ref=request.target_laboratory_ref,
        conversation_ref=request.conversation_ref,
        parent_visit_ref=request.source_visit_ref,
        input_contract_ref=request.input_contract_ref,
        expected_output_contract_ref=request.expected_output_contract_ref,
        return_route_ref=request.return_route_ref,
        visit_mode=request.portable_visit_mode,
        context_refs=request.context_refs,
        evidence_refs=request.evidence_refs,
    )


def build_specialist_transfer_result(
    request: SpecialistTransferRequest,
    plan: SpecialistTransferVisitPlan,
    *,
    status: SpecialistTransferStatus,
    reason: str,
    context_refs: Sequence[str] = (),
    evidence_refs: Sequence[str] = (),
) -> SpecialistTransferResult:
    """Build an immutable transfer result after the existing Scheduler path."""

    issues = validate_specialist_transfer_chain(request, plan)
    if issues:
        raise SpecialistLaboratoryTransferContractError("; ".join(issues))
    active = _expected_active_laboratory(
        mode=request.mode,
        status=status,
        origin=request.origin_laboratory_ref,
        target=request.target_laboratory_ref,
    )
    return SpecialistTransferResult(
        schema=SPECIALIST_TRANSFER_RESULT_SCHEMA,
        transfer_ref=request.transfer_ref,
        mode=request.mode,
        status=status,
        specialist_ref=request.specialist_ref,
        conversation_ref=request.conversation_ref,
        source_visit_ref=request.source_visit_ref,
        target_visit_ref=plan.target_visit_ref,
        origin_laboratory_ref=request.origin_laboratory_ref,
        target_laboratory_ref=request.target_laboratory_ref,
        active_laboratory_ref=active,
        return_route_ref=request.return_route_ref,
        reason=reason,
        context_refs=_merge_refs(request.context_refs, context_refs),
        evidence_refs=_merge_refs(request.evidence_refs, evidence_refs),
    )


def validate_specialist_transfer_chain(
    request: SpecialistTransferRequest,
    plan: SpecialistTransferVisitPlan,
    result: SpecialistTransferResult | None = None,
) -> tuple[str, ...]:
    """Return continuity issues across request, visit plan and optional result."""

    issues: list[str] = []
    if plan.transfer_ref != request.transfer_ref:
        issues.append("visit plan transfer_ref must match request")
    if plan.specialist_ref != request.specialist_ref:
        issues.append("visit plan specialist_ref must match request")
    if plan.conversation_ref != request.conversation_ref:
        issues.append("visit plan conversation_ref must match request")
    if plan.parent_visit_ref != request.source_visit_ref:
        issues.append("visit plan parent_visit_ref must match source visit")
    if plan.origin_laboratory_ref != request.origin_laboratory_ref:
        issues.append("visit plan origin laboratory must match request")
    if plan.target_laboratory_ref != request.target_laboratory_ref:
        issues.append("visit plan target laboratory must match request")
    if plan.visit_mode != request.portable_visit_mode:
        issues.append("visit plan mode must match transfer request")
    if plan.return_route_ref != request.return_route_ref:
        issues.append("visit plan return route must match request")
    if result is not None:
        if result.transfer_ref != request.transfer_ref:
            issues.append("result transfer_ref must match request")
        if result.specialist_ref != request.specialist_ref:
            issues.append("result specialist_ref must match request")
        if result.conversation_ref != request.conversation_ref:
            issues.append("result conversation_ref must match request")
        if result.source_visit_ref != request.source_visit_ref:
            issues.append("result source_visit_ref must match request")
        if result.target_visit_ref != plan.target_visit_ref:
            issues.append("result target_visit_ref must match visit plan")
        if result.return_route_ref != request.return_route_ref:
            issues.append("result return route must match request")
    return tuple(dict.fromkeys(issues))


def _validate_source_links(
    request: LaboratoryTransferSourceRequestLike,
    result: LaboratoryTransferSourceResultLike,
    conversation: SpecialistLaboratoryConversation,
) -> list[str]:
    issues: list[str] = []
    if result.visit_ref != request.visit_ref:
        issues.append("source result visit_ref must match source request")
    if result.laboratory_ref != request.laboratory_ref:
        issues.append("source result laboratory_ref must match source request")
    if result.specialist_ref != request.specialist_ref:
        issues.append("source result specialist_ref must match source request")
    if conversation.visit_ref != request.visit_ref:
        issues.append("conversation visit_ref must match source request")
    if conversation.specialist_ref != request.specialist_ref:
        issues.append("conversation specialist_ref must match source request")
    expected_conversation = request.conversation_ref or conversation.conversation_ref
    if conversation.conversation_ref != expected_conversation:
        issues.append("conversation_ref must match source request")
    if result.conversation_ref not in (None, conversation.conversation_ref):
        issues.append("source result conversation_ref must match conversation")
    return issues


def _expected_active_laboratory(
    *,
    mode: SpecialistTransferMode,
    status: SpecialistTransferStatus,
    origin: str,
    target: str,
) -> str:
    if status == "rejected":
        return origin
    if status == "accepted":
        return target
    return origin if mode == "visit" else target


def _stable_transfer_ref(source_visit_ref: str, target: str, mode: str) -> str:
    digest = hashlib.sha256(
        f"{source_visit_ref}|{target}|{mode}".encode("utf-8")
    ).hexdigest()[:16]
    return f"specialist-transfer:{digest}"


def _merge_refs(*collections: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(ref for values in collections for ref in values))


def _require_typed_ref(
    name: str,
    value: str,
    required_prefixes: tuple[str, ...],
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise SpecialistLaboratoryTransferContractError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(required_prefixes):
        raise SpecialistLaboratoryTransferContractError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SpecialistLaboratoryTransferContractError(f"{name} must be non-empty")
    if len(value) > _MAX_TEXT_CHARS:
        raise SpecialistLaboratoryTransferContractError(
            f"{name} exceeds {_MAX_TEXT_CHARS} characters"
        )


def _normalize_refs(
    name: str,
    refs: Sequence[str],
    prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    values = tuple(dict.fromkeys(refs))
    if len(values) > _MAX_REFS:
        raise SpecialistLaboratoryTransferContractError(
            f"{name} exceeds {_MAX_REFS} references"
        )
    for ref in values:
        _require_typed_ref(name, ref, prefixes)
    return values


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        _require_text("metadata key", key)
        _require_text("metadata value", value)
        normalized[key.strip()] = value.strip()
    return tuple(normalized.items())


__all__ = (
    "SPECIALIST_LABORATORY_TRANSFER_CONTRACT_VERSION",
    "SPECIALIST_TRANSFER_REQUEST_SCHEMA",
    "SPECIALIST_TRANSFER_RESULT_SCHEMA",
    "SPECIALIST_TRANSFER_VISIT_PLAN_SCHEMA",
    "LaboratoryTransferSourceRequestLike",
    "LaboratoryTransferSourceResultLike",
    "SpecialistLaboratoryTransferContractError",
    "SpecialistTransferMode",
    "SpecialistTransferRequest",
    "SpecialistTransferResult",
    "SpecialistTransferStatus",
    "SpecialistTransferVisitPlan",
    "build_specialist_transfer_request",
    "build_specialist_transfer_result",
    "build_specialist_transfer_visit_plan",
    "validate_specialist_transfer_chain",
)
