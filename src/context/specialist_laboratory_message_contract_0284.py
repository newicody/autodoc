"""Immutable specialist/laboratory message contracts for phase 0284-r3.

The message envelope bridges the portable specialist descriptor introduced by
0284-r2 with the existing laboratory visit and specialist route-frame
vocabulary.  It is a pure contract/projection surface: it does not write route
frames, publish commands on EventBus, attach a provider, mutate Scheduler.run(),
write SQL/Qdrant, call OpenVINO, call GitHub, or create a transport.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import re
from types import MappingProxyType
from typing import Any, Literal, Protocol

from context.portable_specialist_contract_0284 import (
    PortableSpecialistDescriptor,
    SpecialistLaboratoryVisitMode,
    validate_portable_specialist_visit_contract,
)

SPECIALIST_LABORATORY_MESSAGE_CONTRACT_VERSION = "0284.r3"
SPECIALIST_LABORATORY_MESSAGE_SCHEMA = "missipy.specialist.laboratory_message.v1"
SPECIALIST_LABORATORY_CONVERSATION_SCHEMA = (
    "missipy.specialist.laboratory_conversation.v1"
)

SpecialistLaboratoryMessageKind = Literal[
    "demand",
    "opinion",
    "context_request",
    "specialist_request",
    "laboratory_request",
    "result",
    "acknowledgement",
]

_ALLOWED_MESSAGE_KINDS = frozenset(
    {
        "demand",
        "opinion",
        "context_request",
        "specialist_request",
        "laboratory_request",
        "result",
        "acknowledgement",
    }
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_MESSAGE_PREFIXES = ("laboratory-message:",)
_CONVERSATION_PREFIXES = ("laboratory-conversation:",)
_VISIT_PREFIXES = ("laboratory-visit:",)
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_LABORATORY_PREFIXES = ("laboratory:",)
_CONTRACT_PREFIXES = ("contract:",)
_ROUTE_PREFIXES = ("route:", "specialist-path:")
_ROUTE_FRAME_PREFIXES = ("route-frame:",)
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
_OBSERVATION_PREFIXES = ("bus:", "specialist-path:", "scheduler-trace:")
_PARTICIPANT_PREFIXES = _SPECIALIST_PREFIXES + _LABORATORY_PREFIXES
_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))
_MAX_SEQUENCE_NO = 2_147_483_647
_MAX_TEXT_CHARS = 1_000_000
_MAX_REFS = 1_024


class SpecialistLaboratoryMessageContractError(ValueError):
    """Raised when a specialist/laboratory message contract is incoherent."""


class LaboratoryVisitRequestLike(Protocol):
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


class LaboratoryVisitResultLike(Protocol):
    visit_ref: str
    laboratory_ref: str
    specialist_ref: str
    status: str
    output_contract_ref: str
    machine_result: Mapping[str, Any]
    human_representation: str
    confidence: float
    evidence_refs: Sequence[str]
    requested_context_refs: Sequence[str]
    conversation_ref: str | None


class SpecialistDemandFrameLike(Protocol):
    frame_ref: str
    route_ref: str
    specialist_ref: str
    request_text: str
    context_refs: Sequence[str]
    embedding_model_ref: str
    qdrant_collection_ref: str
    expected_output: str
    depth: str


class SpecialistOpinionFrameLike(Protocol):
    frame_ref: str
    route_ref: str
    demand_frame_ref: str
    specialist_ref: str
    opinion_ref: str
    stance: str
    summary: str
    context_delta_refs: Sequence[str]
    observation_fact_refs: Sequence[str]


@dataclass(frozen=True, slots=True)
class SpecialistLaboratoryMessage:
    """One immutable message exchanged around a bounded laboratory visit."""

    schema: str
    message_ref: str
    conversation_ref: str
    visit_ref: str
    sequence_no: int
    kind: SpecialistLaboratoryMessageKind
    specialist_ref: str
    origin_laboratory_ref: str
    target_laboratory_ref: str
    sender_ref: str
    recipient_ref: str
    contract_ref: str
    return_route_ref: str
    human_representation: str
    payload: Mapping[str, Any]
    route_ref: str | None = None
    route_frame_ref: str | None = None
    reply_to_message_ref: str | None = None
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    observation_fact_refs: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_LABORATORY_MESSAGE_SCHEMA:
            raise SpecialistLaboratoryMessageContractError(
                "unsupported specialist laboratory message schema"
            )
        _require_typed_ref(
            "message_ref", self.message_ref, required_prefixes=_MESSAGE_PREFIXES
        )
        _require_typed_ref(
            "conversation_ref",
            self.conversation_ref,
            required_prefixes=_CONVERSATION_PREFIXES,
        )
        _require_typed_ref("visit_ref", self.visit_ref, required_prefixes=_VISIT_PREFIXES)
        _require_int_range(
            "sequence_no", self.sequence_no, minimum=0, maximum=_MAX_SEQUENCE_NO
        )
        if self.kind not in _ALLOWED_MESSAGE_KINDS:
            raise SpecialistLaboratoryMessageContractError(
                "unsupported specialist laboratory message kind"
            )
        _require_typed_ref(
            "specialist_ref", self.specialist_ref, required_prefixes=_SPECIALIST_PREFIXES
        )
        _require_typed_ref(
            "origin_laboratory_ref",
            self.origin_laboratory_ref,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        _require_typed_ref(
            "target_laboratory_ref",
            self.target_laboratory_ref,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        _require_typed_ref(
            "sender_ref", self.sender_ref, required_prefixes=_PARTICIPANT_PREFIXES
        )
        _require_typed_ref(
            "recipient_ref", self.recipient_ref, required_prefixes=_PARTICIPANT_PREFIXES
        )
        if self.sender_ref == self.recipient_ref:
            raise SpecialistLaboratoryMessageContractError(
                "sender_ref and recipient_ref must differ"
            )
        _validate_participant_direction(self)
        _require_typed_ref(
            "contract_ref", self.contract_ref, required_prefixes=_CONTRACT_PREFIXES
        )
        _require_typed_ref(
            "return_route_ref",
            self.return_route_ref,
            required_prefixes=_ROUTE_PREFIXES,
        )
        _require_text("human_representation", self.human_representation)
        if not isinstance(self.payload, Mapping):
            raise SpecialistLaboratoryMessageContractError("payload must be a mapping")
        object.__setattr__(self, "payload", _freeze_json_mapping(self.payload))
        if self.route_ref is not None:
            _require_typed_ref(
                "route_ref", self.route_ref, required_prefixes=_ROUTE_PREFIXES
            )
        if self.route_frame_ref is not None:
            _require_typed_ref(
                "route_frame_ref",
                self.route_frame_ref,
                required_prefixes=_ROUTE_FRAME_PREFIXES,
            )
            if self.route_ref is None:
                raise SpecialistLaboratoryMessageContractError(
                    "route_frame_ref requires route_ref"
                )
        if self.reply_to_message_ref is not None:
            _require_typed_ref(
                "reply_to_message_ref",
                self.reply_to_message_ref,
                required_prefixes=_MESSAGE_PREFIXES,
            )
            if self.reply_to_message_ref == self.message_ref:
                raise SpecialistLaboratoryMessageContractError(
                    "reply_to_message_ref must not equal message_ref"
                )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs(
                "context_refs",
                self.context_refs,
                allow_empty=True,
                required_prefixes=_CONTEXT_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs",
                self.evidence_refs,
                allow_empty=True,
                required_prefixes=_EVIDENCE_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "observation_fact_refs",
            _normalize_refs(
                "observation_fact_refs",
                self.observation_fact_refs,
                allow_empty=True,
                required_prefixes=_OBSERVATION_PREFIXES,
            ),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "message_ref": self.message_ref,
            "conversation_ref": self.conversation_ref,
            "visit_ref": self.visit_ref,
            "sequence_no": self.sequence_no,
            "kind": self.kind,
            "specialist_ref": self.specialist_ref,
            "origin_laboratory_ref": self.origin_laboratory_ref,
            "target_laboratory_ref": self.target_laboratory_ref,
            "sender_ref": self.sender_ref,
            "recipient_ref": self.recipient_ref,
            "contract_ref": self.contract_ref,
            "return_route_ref": self.return_route_ref,
            "human_representation": self.human_representation,
            "payload": _thaw_json(self.payload),
            "route_ref": self.route_ref,
            "route_frame_ref": self.route_frame_ref,
            "reply_to_message_ref": self.reply_to_message_ref,
            "context_refs": list(self.context_refs),
            "evidence_refs": list(self.evidence_refs),
            "observation_fact_refs": list(self.observation_fact_refs),
            "metadata": dict(self.metadata),
            "transport_created": False,
            "eventbus_command": False,
            "durable_authority": False,
            "scheduler_remains_orchestrator": True,
        }


@dataclass(frozen=True, slots=True)
class SpecialistLaboratoryConversation:
    """Ordered immutable conversation for one specialist visit."""

    schema: str
    conversation_ref: str
    visit_ref: str
    specialist_ref: str
    messages: tuple[SpecialistLaboratoryMessage, ...]

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_LABORATORY_CONVERSATION_SCHEMA:
            raise SpecialistLaboratoryMessageContractError(
                "unsupported specialist laboratory conversation schema"
            )
        _require_typed_ref(
            "conversation_ref",
            self.conversation_ref,
            required_prefixes=_CONVERSATION_PREFIXES,
        )
        _require_typed_ref("visit_ref", self.visit_ref, required_prefixes=_VISIT_PREFIXES)
        _require_typed_ref(
            "specialist_ref", self.specialist_ref, required_prefixes=_SPECIALIST_PREFIXES
        )
        messages = tuple(self.messages)
        if not messages or not all(
            isinstance(item, SpecialistLaboratoryMessage) for item in messages
        ):
            raise SpecialistLaboratoryMessageContractError(
                "messages must contain SpecialistLaboratoryMessage values"
            )
        ordered = tuple(sorted(messages, key=lambda item: item.sequence_no))
        if tuple(item.sequence_no for item in ordered) != tuple(range(len(ordered))):
            raise SpecialistLaboratoryMessageContractError(
                "conversation sequence numbers must be contiguous from zero"
            )
        refs = tuple(item.message_ref for item in ordered)
        if len(set(refs)) != len(refs):
            raise SpecialistLaboratoryMessageContractError(
                "conversation message_ref values must be unique"
            )
        known_refs: set[str] = set()
        for index, message in enumerate(ordered):
            if message.conversation_ref != self.conversation_ref:
                raise SpecialistLaboratoryMessageContractError(
                    "message conversation_ref must match conversation"
                )
            if message.visit_ref != self.visit_ref:
                raise SpecialistLaboratoryMessageContractError(
                    "message visit_ref must match conversation"
                )
            if message.specialist_ref != self.specialist_ref:
                raise SpecialistLaboratoryMessageContractError(
                    "message specialist_ref must match conversation"
                )
            if index == 0 and message.kind != "demand":
                raise SpecialistLaboratoryMessageContractError(
                    "conversation must start with a demand message"
                )
            if index > 0 and message.reply_to_message_ref not in known_refs:
                raise SpecialistLaboratoryMessageContractError(
                    "non-root message must reply to an earlier message"
                )
            known_refs.add(message.message_ref)
        object.__setattr__(self, "messages", ordered)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "conversation_ref": self.conversation_ref,
            "visit_ref": self.visit_ref,
            "specialist_ref": self.specialist_ref,
            "messages": [item.to_mapping() for item in self.messages],
            "message_count": len(self.messages),
            "append_only": True,
            "transport_created": False,
            "eventbus_observation_only": True,
            "sql_remains_authority": True,
        }


def build_specialist_demand_message(
    descriptor: PortableSpecialistDescriptor,
    request: LaboratoryVisitRequestLike,
    demand_frame: SpecialistDemandFrameLike,
    *,
    visit_mode: SpecialistLaboratoryVisitMode,
    sequence_no: int = 0,
    message_ref: str | None = None,
) -> SpecialistLaboratoryMessage:
    """Project an existing visit request and demand frame into one message."""

    issues = validate_portable_specialist_visit_contract(
        descriptor,
        specialist_ref=request.specialist_ref,
        laboratory_ref=request.laboratory_ref,
        input_contract_ref=request.input_contract_ref,
        output_contract_ref=request.expected_output_contract_ref,
        visit_mode=visit_mode,
    )
    if issues:
        raise SpecialistLaboratoryMessageContractError("; ".join(issues))
    if demand_frame.specialist_ref != request.specialist_ref:
        raise SpecialistLaboratoryMessageContractError(
            "demand frame specialist_ref must match visit request"
        )
    origin = request.origin_laboratory_ref or request.laboratory_ref
    target = request.target_laboratory_ref or request.laboratory_ref
    conversation_ref = request.conversation_ref or _stable_conversation_ref(
        request.visit_ref, request.specialist_ref
    )
    resolved_message_ref = message_ref or _stable_message_ref(
        conversation_ref, sequence_no, "demand", demand_frame.frame_ref
    )
    return SpecialistLaboratoryMessage(
        schema=SPECIALIST_LABORATORY_MESSAGE_SCHEMA,
        message_ref=resolved_message_ref,
        conversation_ref=conversation_ref,
        visit_ref=request.visit_ref,
        sequence_no=sequence_no,
        kind="demand",
        specialist_ref=request.specialist_ref,
        origin_laboratory_ref=origin,
        target_laboratory_ref=target,
        sender_ref=request.laboratory_ref,
        recipient_ref=request.specialist_ref,
        contract_ref=request.input_contract_ref,
        return_route_ref=request.return_route_ref,
        human_representation=demand_frame.request_text,
        payload={
            "request_text": demand_frame.request_text,
            "expected_output": demand_frame.expected_output,
            "depth": demand_frame.depth,
            "embedding_model_ref": demand_frame.embedding_model_ref,
            "qdrant_collection_ref": demand_frame.qdrant_collection_ref,
        },
        route_ref=demand_frame.route_ref,
        route_frame_ref=demand_frame.frame_ref,
        context_refs=_merge_refs(request.context_refs, demand_frame.context_refs),
        evidence_refs=tuple(request.evidence_refs),
        metadata=(("visit_mode", visit_mode), ("projection", "existing-demand-frame")),
    )


def build_specialist_opinion_message(
    descriptor: PortableSpecialistDescriptor,
    request: LaboratoryVisitRequestLike,
    result: LaboratoryVisitResultLike,
    opinion_frame: SpecialistOpinionFrameLike,
    *,
    demand_message: SpecialistLaboratoryMessage,
    sequence_no: int = 1,
    message_ref: str | None = None,
) -> SpecialistLaboratoryMessage:
    """Project an existing visit result and opinion frame into one reply."""

    _validate_result_links(request, result, opinion_frame, demand_message)
    if result.output_contract_ref not in descriptor.produced_output_contract_refs:
        raise SpecialistLaboratoryMessageContractError(
            "visit result output_contract_ref is not produced by specialist"
        )
    resolved_message_ref = message_ref or _stable_message_ref(
        demand_message.conversation_ref,
        sequence_no,
        "opinion",
        opinion_frame.frame_ref,
    )
    origin = request.origin_laboratory_ref or request.laboratory_ref
    target = request.target_laboratory_ref or request.laboratory_ref
    return SpecialistLaboratoryMessage(
        schema=SPECIALIST_LABORATORY_MESSAGE_SCHEMA,
        message_ref=resolved_message_ref,
        conversation_ref=demand_message.conversation_ref,
        visit_ref=request.visit_ref,
        sequence_no=sequence_no,
        kind="opinion",
        specialist_ref=request.specialist_ref,
        origin_laboratory_ref=origin,
        target_laboratory_ref=target,
        sender_ref=request.specialist_ref,
        recipient_ref=request.laboratory_ref,
        contract_ref=result.output_contract_ref,
        return_route_ref=request.return_route_ref,
        human_representation=result.human_representation,
        payload={
            "opinion_ref": opinion_frame.opinion_ref,
            "stance": opinion_frame.stance,
            "summary": opinion_frame.summary,
            "visit_status": result.status,
            "confidence": result.confidence,
            "machine_result": result.machine_result,
        },
        route_ref=opinion_frame.route_ref,
        route_frame_ref=opinion_frame.frame_ref,
        reply_to_message_ref=demand_message.message_ref,
        context_refs=_merge_refs(
            result.requested_context_refs, opinion_frame.context_delta_refs
        ),
        evidence_refs=tuple(result.evidence_refs),
        observation_fact_refs=tuple(opinion_frame.observation_fact_refs),
        metadata=(("projection", "existing-opinion-frame"),),
    )


def validate_specialist_laboratory_conversation(
    conversation: SpecialistLaboratoryConversation,
) -> tuple[str, ...]:
    """Return semantic exchange issues not enforced by construction alone."""

    issues: list[str] = []
    demand = conversation.messages[0]
    for message in conversation.messages[1:]:
        if message.origin_laboratory_ref != demand.origin_laboratory_ref:
            issues.append("message origin_laboratory_ref changed inside conversation")
        if message.target_laboratory_ref != demand.target_laboratory_ref:
            issues.append("message target_laboratory_ref changed inside conversation")
        if message.return_route_ref != demand.return_route_ref:
            issues.append("message return_route_ref changed inside conversation")
    return tuple(dict.fromkeys(issues))


def _validate_result_links(
    request: LaboratoryVisitRequestLike,
    result: LaboratoryVisitResultLike,
    opinion_frame: SpecialistOpinionFrameLike,
    demand_message: SpecialistLaboratoryMessage,
) -> None:
    issues: list[str] = []
    if result.visit_ref != request.visit_ref:
        issues.append("visit result visit_ref must match request")
    if result.laboratory_ref != request.laboratory_ref:
        issues.append("visit result laboratory_ref must match request")
    if result.specialist_ref != request.specialist_ref:
        issues.append("visit result specialist_ref must match request")
    if result.conversation_ref not in (None, demand_message.conversation_ref):
        issues.append("visit result conversation_ref must match demand message")
    if opinion_frame.specialist_ref != request.specialist_ref:
        issues.append("opinion frame specialist_ref must match request")
    if opinion_frame.demand_frame_ref != demand_message.route_frame_ref:
        issues.append("opinion frame demand_frame_ref must match demand message")
    if issues:
        raise SpecialistLaboratoryMessageContractError("; ".join(issues))


def _validate_participant_direction(message: SpecialistLaboratoryMessage) -> None:
    if message.kind == "demand":
        if message.sender_ref != message.target_laboratory_ref:
            raise SpecialistLaboratoryMessageContractError(
                "demand sender_ref must be target_laboratory_ref"
            )
        if message.recipient_ref != message.specialist_ref:
            raise SpecialistLaboratoryMessageContractError(
                "demand recipient_ref must be specialist_ref"
            )
    if message.kind in {"opinion", "result"}:
        if message.sender_ref != message.specialist_ref:
            raise SpecialistLaboratoryMessageContractError(
                "opinion/result sender_ref must be specialist_ref"
            )
        if message.recipient_ref != message.target_laboratory_ref:
            raise SpecialistLaboratoryMessageContractError(
                "opinion/result recipient_ref must be target_laboratory_ref"
            )


def _stable_conversation_ref(visit_ref: str, specialist_ref: str) -> str:
    suffix = _stable_suffix(f"{visit_ref}|{specialist_ref}")
    return f"laboratory-conversation:{suffix}"


def _stable_message_ref(
    conversation_ref: str,
    sequence_no: int,
    kind: str,
    source_ref: str,
) -> str:
    suffix = _stable_suffix(
        f"{conversation_ref}|{sequence_no}|{kind}|{source_ref}"
    )
    return f"laboratory-message:{suffix}"


def _stable_suffix(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _merge_refs(*collections: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(ref for values in collections for ref in values))


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SpecialistLaboratoryMessageContractError(f"{name} must be non-empty")
    if len(value) > _MAX_TEXT_CHARS:
        raise SpecialistLaboratoryMessageContractError(
            f"{name} exceeds {_MAX_TEXT_CHARS} characters"
        )


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefixes: tuple[str, ...] | None = None,
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise SpecialistLaboratoryMessageContractError(
            f"{name} must be a typed reference"
        )
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise SpecialistLaboratoryMessageContractError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_int_range(
    name: str,
    value: int,
    *,
    minimum: int,
    maximum: int,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SpecialistLaboratoryMessageContractError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise SpecialistLaboratoryMessageContractError(
            f"{name} must be between {minimum} and {maximum}"
        )


def _normalize_refs(
    name: str,
    refs: Sequence[str],
    *,
    allow_empty: bool,
    required_prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    values = tuple(dict.fromkeys(refs))
    if len(values) > _MAX_REFS:
        raise SpecialistLaboratoryMessageContractError(
            f"{name} exceeds {_MAX_REFS} references"
        )
    if not values and not allow_empty:
        raise SpecialistLaboratoryMessageContractError(f"{name} must not be empty")
    for ref in values:
        _require_typed_ref(name, ref, required_prefixes=required_prefixes)
    return values


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values:
        _require_text("metadata key", key)
        _require_text("metadata value", value)
        normalized.append((key.strip(), value.strip()))
    return tuple(dict(normalized).items())


def _freeze_json_mapping(values: Mapping[str, Any]) -> Mapping[str, Any]:
    frozen: dict[str, Any] = {}
    for key, value in values.items():
        _require_text("payload key", key)
        frozen[key] = _freeze_json(value)
    return MappingProxyType(frozen)


def _freeze_json(value: Any) -> Any:
    if isinstance(value, _JSON_SCALAR_TYPES):
        return value
    if isinstance(value, Mapping):
        return _freeze_json_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    raise SpecialistLaboratoryMessageContractError(
        f"payload contains non-JSON value: {type(value).__name__}"
    )


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


__all__ = (
    "SPECIALIST_LABORATORY_CONVERSATION_SCHEMA",
    "SPECIALIST_LABORATORY_MESSAGE_CONTRACT_VERSION",
    "SPECIALIST_LABORATORY_MESSAGE_SCHEMA",
    "LaboratoryVisitRequestLike",
    "LaboratoryVisitResultLike",
    "SpecialistDemandFrameLike",
    "SpecialistLaboratoryConversation",
    "SpecialistLaboratoryMessage",
    "SpecialistLaboratoryMessageContractError",
    "SpecialistLaboratoryMessageKind",
    "SpecialistOpinionFrameLike",
    "build_specialist_demand_message",
    "build_specialist_opinion_message",
    "validate_specialist_laboratory_conversation",
)
