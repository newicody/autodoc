"""Versioned specialist/laboratory exchange contracts for phase 0287-r7-r8.

The v1 message contract remains readable and unchanged.  This module adds the
public v2 boundary required by concrete laboratories: artifact digests,
correlation and idempotency identities, cross-visit continuation, normalized
completion/error messages and conversations spanning more than one visit.

The module is contract-only.  It creates no transport, Scheduler route,
EventBus command, durable write, inference call or GitHub mutation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Literal

SPECIALIST_LABORATORY_MESSAGE_V2_CONTRACT_VERSION = "0287.r7.r8"
SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA = (
    "missipy.specialist.laboratory_message.v2"
)
SPECIALIST_LABORATORY_CONVERSATION_V2_SCHEMA = (
    "missipy.specialist.laboratory_conversation.v2"
)
SPECIALIST_ARTIFACT_REFERENCE_SCHEMA = (
    "missipy.specialist.artifact_reference.v1"
)
SPECIALIST_EXCHANGE_ERROR_SCHEMA = "missipy.specialist.exchange_error.v1"
SPECIALIST_COMPLETION_CONTRACT_REF = "contract:missipy.specialist.completion.v1"
SPECIALIST_ERROR_CONTRACT_REF = "contract:missipy.specialist.exchange_error.v1"

SpecialistLaboratoryMessageKindV2 = Literal[
    "demand",
    "analysis",
    "context_request",
    "specialist_request",
    "laboratory_request",
    "artifact_delivery",
    "acknowledgement",
    "completion",
    "error",
]

_ALLOWED_MESSAGE_KINDS = frozenset(
    {
        "demand",
        "analysis",
        "context_request",
        "specialist_request",
        "laboratory_request",
        "artifact_delivery",
        "acknowledgement",
        "completion",
        "error",
    }
)
_TERMINAL_MESSAGE_KINDS = frozenset({"completion", "error"})
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_IDEMPOTENCY_RE = re.compile(r"^idempotency:[A-Za-z0-9._:-]{8,240}$")
_MESSAGE_PREFIXES = ("laboratory-message:",)
_CONVERSATION_PREFIXES = ("laboratory-conversation:",)
_VISIT_PREFIXES = ("laboratory-visit:",)
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_LABORATORY_PREFIXES = ("laboratory:",)
_PARTICIPANT_PREFIXES = _SPECIALIST_PREFIXES + _LABORATORY_PREFIXES + (
    "autodoc:",
)
_CONTRACT_PREFIXES = ("contract:",)
_ROUTE_PREFIXES = ("route:", "specialist-path:")
_CORRELATION_PREFIXES = ("correlation:",)
_ARTIFACT_PREFIXES = ("artifact:",)
_STORAGE_PREFIXES = (
    "artifact:",
    "dataset:",
    "raw-dataset:",
    "sql:",
    "ctx:",
    "ctx-result:",
)
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
_PROVENANCE_PREFIXES = _EVIDENCE_PREFIXES + (
    "laboratory-message:",
    "laboratory-visit:",
    "specialist-contribution:",
)
_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))
_MAX_REFS = 1_024
_MAX_TEXT_CHARS = 1_000_000
_MAX_SEQUENCE_NO = 2_147_483_647


class SpecialistLaboratoryMessageV2ContractError(ValueError):
    """Raised when one v2 exchange contract is incoherent."""


@dataclass(frozen=True, slots=True)
class SpecialistArtifactReference:
    """Portable digest-backed reference to one exchanged artifact."""

    schema: str
    artifact_ref: str
    artifact_schema: str
    producer_ref: str
    storage_ref: str
    content_sha256: str
    media_type: str
    byte_count: int
    producer_visit_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_ARTIFACT_REFERENCE_SCHEMA:
            raise SpecialistLaboratoryMessageV2ContractError(
                "unsupported specialist artifact reference schema"
            )
        _require_typed_ref(
            "artifact_ref", self.artifact_ref, required_prefixes=_ARTIFACT_PREFIXES
        )
        _require_text("artifact_schema", self.artifact_schema)
        _require_typed_ref(
            "producer_ref", self.producer_ref, required_prefixes=_PARTICIPANT_PREFIXES
        )
        _require_typed_ref(
            "storage_ref", self.storage_ref, required_prefixes=_STORAGE_PREFIXES
        )
        _require_sha256("content_sha256", self.content_sha256)
        _require_text("media_type", self.media_type)
        if isinstance(self.byte_count, bool) or not isinstance(self.byte_count, int):
            raise SpecialistLaboratoryMessageV2ContractError(
                "byte_count must be an integer"
            )
        if self.byte_count < 0:
            raise SpecialistLaboratoryMessageV2ContractError(
                "byte_count must be non-negative"
            )
        if self.producer_visit_ref is not None:
            _require_typed_ref(
                "producer_visit_ref",
                self.producer_visit_ref,
                required_prefixes=_VISIT_PREFIXES,
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs",
                self.evidence_refs,
                required_prefixes=_EVIDENCE_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "provenance_refs",
            _normalize_refs(
                "provenance_refs",
                self.provenance_refs,
                required_prefixes=_PROVENANCE_PREFIXES,
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "artifact_ref": self.artifact_ref,
            "artifact_schema": self.artifact_schema,
            "producer_ref": self.producer_ref,
            "producer_visit_ref": self.producer_visit_ref,
            "storage_ref": self.storage_ref,
            "content_sha256": self.content_sha256,
            "media_type": self.media_type,
            "byte_count": self.byte_count,
            "evidence_refs": list(self.evidence_refs),
            "provenance_refs": list(self.provenance_refs),
            "inline_bytes_present": False,
            "durable_authority_claimed": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistExchangeError:
    """Normalized error attached only to one v2 error message."""

    schema: str
    error_code: str
    retryable: bool
    human_message: str
    failed_message_ref: str
    requested_action: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_EXCHANGE_ERROR_SCHEMA:
            raise SpecialistLaboratoryMessageV2ContractError(
                "unsupported specialist exchange error schema"
            )
        _require_identifier("error_code", self.error_code)
        if not isinstance(self.retryable, bool):
            raise SpecialistLaboratoryMessageV2ContractError(
                "retryable must be a boolean"
            )
        _require_text("human_message", self.human_message)
        _require_typed_ref(
            "failed_message_ref",
            self.failed_message_ref,
            required_prefixes=_MESSAGE_PREFIXES,
        )
        _require_identifier("requested_action", self.requested_action)
        if not isinstance(self.details, Mapping):
            raise SpecialistLaboratoryMessageV2ContractError(
                "error details must be a mapping"
            )
        object.__setattr__(self, "details", _freeze_json_mapping(self.details))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "error_code": self.error_code,
            "retryable": self.retryable,
            "human_message": self.human_message,
            "failed_message_ref": self.failed_message_ref,
            "requested_action": self.requested_action,
            "details": _thaw_json(self.details),
        }


@dataclass(frozen=True, slots=True)
class SpecialistLaboratoryMessageV2:
    """One immutable v2 message, possibly continuing a previous visit."""

    schema: str
    message_ref: str
    conversation_ref: str
    visit_ref: str
    sequence_no: int
    kind: SpecialistLaboratoryMessageKindV2
    specialist_ref: str
    origin_laboratory_ref: str
    target_laboratory_ref: str
    sender_ref: str
    recipient_ref: str
    payload_contract_ref: str
    return_route_ref: str
    correlation_ref: str
    idempotency_key: str
    human_representation: str
    payload: Mapping[str, Any]
    payload_sha256: str
    reply_to_message_ref: str | None = None
    parent_visit_ref: str | None = None
    continuation_of_message_ref: str | None = None
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    artifact_refs: tuple[SpecialistArtifactReference, ...] = ()
    error: SpecialistExchangeError | None = None
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA:
            raise SpecialistLaboratoryMessageV2ContractError(
                "unsupported specialist laboratory message v2 schema"
            )
        _require_typed_ref(
            "message_ref", self.message_ref, required_prefixes=_MESSAGE_PREFIXES
        )
        _require_typed_ref(
            "conversation_ref",
            self.conversation_ref,
            required_prefixes=_CONVERSATION_PREFIXES,
        )
        _require_typed_ref("visit_ref", self.visit_ref, _VISIT_PREFIXES)
        _require_int_range(
            "sequence_no", self.sequence_no, minimum=0, maximum=_MAX_SEQUENCE_NO
        )
        if self.kind not in _ALLOWED_MESSAGE_KINDS:
            raise SpecialistLaboratoryMessageV2ContractError(
                "unsupported specialist laboratory message v2 kind"
            )
        _require_typed_ref(
            "specialist_ref", self.specialist_ref, _SPECIALIST_PREFIXES
        )
        _require_typed_ref(
            "origin_laboratory_ref",
            self.origin_laboratory_ref,
            _LABORATORY_PREFIXES,
        )
        _require_typed_ref(
            "target_laboratory_ref",
            self.target_laboratory_ref,
            _LABORATORY_PREFIXES,
        )
        _require_typed_ref("sender_ref", self.sender_ref, _PARTICIPANT_PREFIXES)
        _require_typed_ref(
            "recipient_ref", self.recipient_ref, _PARTICIPANT_PREFIXES
        )
        if self.sender_ref == self.recipient_ref:
            raise SpecialistLaboratoryMessageV2ContractError(
                "sender_ref and recipient_ref must differ"
            )
        _validate_participant_direction(self)
        _require_typed_ref(
            "payload_contract_ref",
            self.payload_contract_ref,
            _CONTRACT_PREFIXES,
        )
        _require_typed_ref(
            "return_route_ref", self.return_route_ref, _ROUTE_PREFIXES
        )
        _require_typed_ref(
            "correlation_ref", self.correlation_ref, _CORRELATION_PREFIXES
        )
        if not isinstance(self.idempotency_key, str) or not _IDEMPOTENCY_RE.fullmatch(
            self.idempotency_key
        ):
            raise SpecialistLaboratoryMessageV2ContractError(
                "idempotency_key must be an idempotency: typed stable key"
            )
        _require_text("human_representation", self.human_representation)
        if not isinstance(self.payload, Mapping):
            raise SpecialistLaboratoryMessageV2ContractError(
                "payload must be a mapping"
            )
        frozen_payload = _freeze_json_mapping(self.payload)
        object.__setattr__(self, "payload", frozen_payload)
        _require_sha256("payload_sha256", self.payload_sha256)
        expected_digest = compute_payload_sha256(frozen_payload)
        if self.payload_sha256 != expected_digest:
            raise SpecialistLaboratoryMessageV2ContractError(
                "payload_sha256 does not match the canonical payload"
            )
        if self.reply_to_message_ref is not None:
            _require_typed_ref(
                "reply_to_message_ref",
                self.reply_to_message_ref,
                _MESSAGE_PREFIXES,
            )
            if self.reply_to_message_ref == self.message_ref:
                raise SpecialistLaboratoryMessageV2ContractError(
                    "reply_to_message_ref must not equal message_ref"
                )
        continuation_values = (
            self.parent_visit_ref,
            self.continuation_of_message_ref,
        )
        if any(value is None for value in continuation_values) and any(
            value is not None for value in continuation_values
        ):
            raise SpecialistLaboratoryMessageV2ContractError(
                "cross-visit continuation requires parent_visit_ref and "
                "continuation_of_message_ref together"
            )
        if self.parent_visit_ref is not None:
            _require_typed_ref(
                "parent_visit_ref", self.parent_visit_ref, _VISIT_PREFIXES
            )
            _require_typed_ref(
                "continuation_of_message_ref",
                self.continuation_of_message_ref or "",
                _MESSAGE_PREFIXES,
            )
            if self.parent_visit_ref == self.visit_ref:
                raise SpecialistLaboratoryMessageV2ContractError(
                    "parent_visit_ref must differ from visit_ref"
                )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs(
                "context_refs", self.context_refs, _CONTEXT_PREFIXES
            ),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs", self.evidence_refs, _EVIDENCE_PREFIXES
            ),
        )
        artifacts = tuple(self.artifact_refs)
        if not all(isinstance(item, SpecialistArtifactReference) for item in artifacts):
            raise SpecialistLaboratoryMessageV2ContractError(
                "artifact_refs must contain SpecialistArtifactReference values"
            )
        artifact_ids = tuple(item.artifact_ref for item in artifacts)
        if len(set(artifact_ids)) != len(artifact_ids):
            raise SpecialistLaboratoryMessageV2ContractError(
                "artifact_ref values must be unique in one message"
            )
        object.__setattr__(self, "artifact_refs", artifacts)
        if self.kind == "error" and self.error is None:
            raise SpecialistLaboratoryMessageV2ContractError(
                "error messages require a normalized error"
            )
        if self.kind != "error" and self.error is not None:
            raise SpecialistLaboratoryMessageV2ContractError(
                "normalized error is allowed only on error messages"
            )
        if self.error is not None and not isinstance(
            self.error, SpecialistExchangeError
        ):
            raise SpecialistLaboratoryMessageV2ContractError(
                "error must be a SpecialistExchangeError"
            )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def terminal(self) -> bool:
        return self.kind in _TERMINAL_MESSAGE_KINDS

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
            "payload_contract_ref": self.payload_contract_ref,
            "return_route_ref": self.return_route_ref,
            "correlation_ref": self.correlation_ref,
            "idempotency_key": self.idempotency_key,
            "human_representation": self.human_representation,
            "payload": _thaw_json(self.payload),
            "payload_sha256": self.payload_sha256,
            "reply_to_message_ref": self.reply_to_message_ref,
            "parent_visit_ref": self.parent_visit_ref,
            "continuation_of_message_ref": self.continuation_of_message_ref,
            "context_refs": list(self.context_refs),
            "evidence_refs": list(self.evidence_refs),
            "artifact_refs": [item.to_mapping() for item in self.artifact_refs],
            "error": self.error.to_mapping() if self.error is not None else None,
            "metadata": dict(self.metadata),
            "terminal": self.terminal,
            "transport_created": False,
            "scheduler_command_emitted": False,
            "eventbus_command": False,
            "durable_authority_claimed": False,
            "scheduler_remains_orchestrator": True,
        }


@dataclass(frozen=True, slots=True)
class SpecialistLaboratoryConversationV2:
    """Ordered v2 conversation that may continue across visits/specialists."""

    schema: str
    conversation_ref: str
    correlation_ref: str
    return_route_ref: str
    messages: tuple[SpecialistLaboratoryMessageV2, ...]
    closed: bool = False

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_LABORATORY_CONVERSATION_V2_SCHEMA:
            raise SpecialistLaboratoryMessageV2ContractError(
                "unsupported specialist laboratory conversation v2 schema"
            )
        _require_typed_ref(
            "conversation_ref", self.conversation_ref, _CONVERSATION_PREFIXES
        )
        _require_typed_ref(
            "correlation_ref", self.correlation_ref, _CORRELATION_PREFIXES
        )
        _require_typed_ref(
            "return_route_ref", self.return_route_ref, _ROUTE_PREFIXES
        )
        if not isinstance(self.closed, bool):
            raise SpecialistLaboratoryMessageV2ContractError(
                "closed must be a boolean"
            )
        messages = tuple(self.messages)
        if not messages or not all(
            isinstance(item, SpecialistLaboratoryMessageV2) for item in messages
        ):
            raise SpecialistLaboratoryMessageV2ContractError(
                "messages must contain SpecialistLaboratoryMessageV2 values"
            )
        ordered = tuple(sorted(messages, key=lambda item: item.sequence_no))
        if tuple(item.sequence_no for item in ordered) != tuple(range(len(ordered))):
            raise SpecialistLaboratoryMessageV2ContractError(
                "conversation sequence numbers must be contiguous from zero"
            )
        message_refs = tuple(item.message_ref for item in ordered)
        if len(set(message_refs)) != len(message_refs):
            raise SpecialistLaboratoryMessageV2ContractError(
                "conversation message_ref values must be unique"
            )
        idempotency_keys = tuple(item.idempotency_key for item in ordered)
        if len(set(idempotency_keys)) != len(idempotency_keys):
            raise SpecialistLaboratoryMessageV2ContractError(
                "conversation idempotency keys must be unique"
            )
        known_messages: dict[str, SpecialistLaboratoryMessageV2] = {}
        known_visits: set[str] = set()
        for index, message in enumerate(ordered):
            if message.conversation_ref != self.conversation_ref:
                raise SpecialistLaboratoryMessageV2ContractError(
                    "message conversation_ref must match conversation"
                )
            if message.correlation_ref != self.correlation_ref:
                raise SpecialistLaboratoryMessageV2ContractError(
                    "message correlation_ref must match conversation"
                )
            if message.return_route_ref != self.return_route_ref:
                raise SpecialistLaboratoryMessageV2ContractError(
                    "message return_route_ref must match conversation"
                )
            if index == 0:
                if message.kind != "demand":
                    raise SpecialistLaboratoryMessageV2ContractError(
                        "conversation must start with a demand message"
                    )
                if message.reply_to_message_ref is not None:
                    raise SpecialistLaboratoryMessageV2ContractError(
                        "root demand must not reply to another message"
                    )
                if message.parent_visit_ref is not None:
                    raise SpecialistLaboratoryMessageV2ContractError(
                        "root demand must not continue another visit"
                    )
            else:
                links = (
                    message.reply_to_message_ref,
                    message.continuation_of_message_ref,
                )
                if not any(link in known_messages for link in links if link):
                    raise SpecialistLaboratoryMessageV2ContractError(
                        "non-root messages must link to an earlier message"
                    )
            if message.parent_visit_ref is not None:
                if message.parent_visit_ref not in known_visits:
                    raise SpecialistLaboratoryMessageV2ContractError(
                        "parent_visit_ref must identify an earlier visit"
                    )
                continued = known_messages.get(
                    message.continuation_of_message_ref or ""
                )
                if continued is None or continued.visit_ref != message.parent_visit_ref:
                    raise SpecialistLaboratoryMessageV2ContractError(
                        "continuation message must belong to parent_visit_ref"
                    )
            known_messages[message.message_ref] = message
            known_visits.add(message.visit_ref)
        if self.closed and not ordered[-1].terminal:
            raise SpecialistLaboratoryMessageV2ContractError(
                "closed conversation must end with completion or error"
            )
        if not self.closed and ordered[-1].terminal:
            raise SpecialistLaboratoryMessageV2ContractError(
                "terminal final message requires closed=true"
            )
        object.__setattr__(self, "messages", ordered)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "conversation_ref": self.conversation_ref,
            "correlation_ref": self.correlation_ref,
            "return_route_ref": self.return_route_ref,
            "messages": [item.to_mapping() for item in self.messages],
            "message_count": len(self.messages),
            "visit_refs": list(dict.fromkeys(item.visit_ref for item in self.messages)),
            "specialist_refs": list(
                dict.fromkeys(item.specialist_ref for item in self.messages)
            ),
            "closed": self.closed,
            "append_only": True,
            "cross_visit_continuation_supported": True,
            "scheduler_remains_orchestrator": True,
            "transport_created": False,
            "eventbus_observation_only": True,
            "sql_remains_authority": True,
        }


def compute_payload_sha256(payload: Mapping[str, Any]) -> str:
    """Return the stable digest of one JSON-compatible payload mapping."""

    if not isinstance(payload, Mapping):
        raise SpecialistLaboratoryMessageV2ContractError(
            "payload must be a mapping"
        )
    frozen = _freeze_json_mapping(payload)
    encoded = json.dumps(
        _thaw_json(frozen),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stable_idempotency_key(*parts: str) -> str:
    """Build one deterministic exchange idempotency identity."""

    if not parts:
        raise SpecialistLaboratoryMessageV2ContractError(
            "at least one idempotency seed part is required"
        )
    for part in parts:
        _require_text("idempotency seed", part)
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"idempotency:{digest}"


def build_completion_message_v2(
    *,
    demand_message: SpecialistLaboratoryMessageV2,
    message_ref: str,
    sequence_no: int,
    specialist_ref: str,
    visit_ref: str,
    human_representation: str,
    artifact_refs: Sequence[SpecialistArtifactReference],
    payload: Mapping[str, Any] | None = None,
) -> SpecialistLaboratoryMessageV2:
    """Build a normalized completion reply without scheduling side effects."""

    completion_payload = dict(payload or {})
    completion_payload.setdefault("status", "completed")
    return SpecialistLaboratoryMessageV2(
        schema=SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA,
        message_ref=message_ref,
        conversation_ref=demand_message.conversation_ref,
        visit_ref=visit_ref,
        sequence_no=sequence_no,
        kind="completion",
        specialist_ref=specialist_ref,
        origin_laboratory_ref=demand_message.origin_laboratory_ref,
        target_laboratory_ref=demand_message.target_laboratory_ref,
        sender_ref=specialist_ref,
        recipient_ref=demand_message.target_laboratory_ref,
        payload_contract_ref=SPECIALIST_COMPLETION_CONTRACT_REF,
        return_route_ref=demand_message.return_route_ref,
        correlation_ref=demand_message.correlation_ref,
        idempotency_key=stable_idempotency_key(
            demand_message.correlation_ref,
            message_ref,
            "completion",
        ),
        human_representation=human_representation,
        payload=completion_payload,
        payload_sha256=compute_payload_sha256(completion_payload),
        reply_to_message_ref=demand_message.message_ref,
        artifact_refs=tuple(artifact_refs),
    )


def build_error_message_v2(
    *,
    demand_message: SpecialistLaboratoryMessageV2,
    message_ref: str,
    sequence_no: int,
    specialist_ref: str,
    visit_ref: str,
    error: SpecialistExchangeError,
) -> SpecialistLaboratoryMessageV2:
    """Build a normalized terminal error reply."""

    payload = {
        "status": "failed",
        "error_code": error.error_code,
        "retryable": error.retryable,
    }
    return SpecialistLaboratoryMessageV2(
        schema=SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA,
        message_ref=message_ref,
        conversation_ref=demand_message.conversation_ref,
        visit_ref=visit_ref,
        sequence_no=sequence_no,
        kind="error",
        specialist_ref=specialist_ref,
        origin_laboratory_ref=demand_message.origin_laboratory_ref,
        target_laboratory_ref=demand_message.target_laboratory_ref,
        sender_ref=specialist_ref,
        recipient_ref=demand_message.target_laboratory_ref,
        payload_contract_ref=SPECIALIST_ERROR_CONTRACT_REF,
        return_route_ref=demand_message.return_route_ref,
        correlation_ref=demand_message.correlation_ref,
        idempotency_key=stable_idempotency_key(
            demand_message.correlation_ref,
            message_ref,
            "error",
        ),
        human_representation=error.human_message,
        payload=payload,
        payload_sha256=compute_payload_sha256(payload),
        reply_to_message_ref=demand_message.message_ref,
        error=error,
    )


def _validate_participant_direction(message: SpecialistLaboratoryMessageV2) -> None:
    if message.kind == "demand":
        if message.sender_ref != message.target_laboratory_ref:
            raise SpecialistLaboratoryMessageV2ContractError(
                "demand sender_ref must be target_laboratory_ref"
            )
        if message.recipient_ref != message.specialist_ref:
            raise SpecialistLaboratoryMessageV2ContractError(
                "demand recipient_ref must be specialist_ref"
            )
    if message.kind in {
        "analysis",
        "artifact_delivery",
        "completion",
    }:
        if message.sender_ref != message.specialist_ref:
            raise SpecialistLaboratoryMessageV2ContractError(
                "analysis/artifact/completion sender must be specialist_ref"
            )
        if message.recipient_ref != message.target_laboratory_ref:
            raise SpecialistLaboratoryMessageV2ContractError(
                "analysis/artifact/completion recipient must be target laboratory"
            )


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SpecialistLaboratoryMessageV2ContractError(
            f"{name} must be non-empty"
        )
    if len(value) > _MAX_TEXT_CHARS:
        raise SpecialistLaboratoryMessageV2ContractError(
            f"{name} exceeds {_MAX_TEXT_CHARS} characters"
        )


def _require_identifier(name: str, value: str) -> None:
    _require_text(name, value)
    if not re.fullmatch(r"[a-z][a-z0-9_.-]*", value):
        raise SpecialistLaboratoryMessageV2ContractError(
            f"{name} must be a lowercase identifier"
        )


def _require_typed_ref(
    name: str,
    value: str,
    required_prefixes: tuple[str, ...],
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise SpecialistLaboratoryMessageV2ContractError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(required_prefixes):
        raise SpecialistLaboratoryMessageV2ContractError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_sha256(name: str, value: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise SpecialistLaboratoryMessageV2ContractError(
            f"{name} must be a lowercase SHA-256 digest"
        )


def _require_int_range(
    name: str,
    value: int,
    *,
    minimum: int,
    maximum: int,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SpecialistLaboratoryMessageV2ContractError(
            f"{name} must be an integer"
        )
    if not minimum <= value <= maximum:
        raise SpecialistLaboratoryMessageV2ContractError(
            f"{name} must be between {minimum} and {maximum}"
        )


def _normalize_refs(
    name: str,
    refs: Sequence[str],
    required_prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(refs, (str, bytes)):
        raise SpecialistLaboratoryMessageV2ContractError(
            f"{name} must be a sequence of references"
        )
    values = tuple(dict.fromkeys(refs))
    if len(values) > _MAX_REFS:
        raise SpecialistLaboratoryMessageV2ContractError(
            f"{name} exceeds {_MAX_REFS} references"
        )
    for ref in values:
        _require_typed_ref(name, ref, required_prefixes)
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
    raise SpecialistLaboratoryMessageV2ContractError(
        f"payload contains non-JSON value: {type(value).__name__}"
    )


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


__all__ = (
    "SPECIALIST_ARTIFACT_REFERENCE_SCHEMA",
    "SPECIALIST_COMPLETION_CONTRACT_REF",
    "SPECIALIST_ERROR_CONTRACT_REF",
    "SPECIALIST_EXCHANGE_ERROR_SCHEMA",
    "SPECIALIST_LABORATORY_CONVERSATION_V2_SCHEMA",
    "SPECIALIST_LABORATORY_MESSAGE_V2_CONTRACT_VERSION",
    "SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA",
    "SpecialistArtifactReference",
    "SpecialistExchangeError",
    "SpecialistLaboratoryConversationV2",
    "SpecialistLaboratoryMessageKindV2",
    "SpecialistLaboratoryMessageV2",
    "SpecialistLaboratoryMessageV2ContractError",
    "build_completion_message_v2",
    "build_error_message_v2",
    "compute_payload_sha256",
    "stable_idempotency_key",
)
