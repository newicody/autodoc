"""Immutable canonical evidence aggregation contracts for phase 0287-r2.

The contract composes existing digest-bound specialist evidence references into
one deterministic multi-provenance candidate. It does not validate the full
laboratory/visit provenance chain, deduplicate content, detect contradictions,
apply weights, write durable state, select through Scheduler, publish EventBus
facts, or mutate GitHub Projects.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Literal

from context.specialist_capability_growth_proposal_contract_0285 import (
    SpecialistCapabilityEvidenceRef,
)

MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA = (
    "missipy.multi_laboratory.evidence_item.v1"
)
MULTI_LABORATORY_EVIDENCE_AGGREGATE_SCHEMA = (
    "missipy.multi_laboratory.evidence_aggregate.v1"
)
MULTI_LABORATORY_EVIDENCE_AGGREGATION_CONTRACT_VERSION = "0287.r2"

MultiLaboratoryEvidenceKind = Literal[
    "artifact",
    "benchmark",
    "execution_result",
    "observation",
    "operator_review",
    "test_report",
]
MultiLaboratoryEvidenceClaimRelation = Literal[
    "supports",
    "opposes",
    "observes",
    "measures",
]

_ALLOWED_EVIDENCE_KINDS = frozenset(
    {
        "artifact",
        "benchmark",
        "execution_result",
        "observation",
        "operator_review",
        "test_report",
    }
)
_ALLOWED_CLAIM_RELATIONS = frozenset(
    {"supports", "opposes", "observes", "measures"}
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_CLAIM_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_EVIDENCE_PREFIXES = (
    "artifact:",
    "evidence:",
    "observation:",
    "report:",
    "result:",
    "sql:",
    "test:",
)
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_SOURCE_PREFIXES = (
    "artifact:",
    "conversation:",
    "event:",
    "github:",
    "observation:",
    "report:",
    "result:",
    "sql:",
    "test:",
)
_PROVENANCE_PREFIXES = ("provenance:",)
_AGGREGATION_PREFIXES = ("aggregation:",)
_SUBJECT_PREFIXES = (
    "artifact:",
    "context:",
    "github:",
    "issue:",
    "proposal:",
    "research:",
    "requirement:",
    "specialist:",
)
_CONVERSATION_PREFIXES = ("conversation:",)
_CONTEXT_PREFIXES = ("context:", "sql:")
_POLICY_PREFIXES = ("policy:",)


class MultiLaboratoryEvidenceAggregationContractError(ValueError):
    """Raised when an evidence item or aggregate is incoherent."""


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceItem:
    """One immutable claim envelope with opaque provenance reference.

    The provenance reference is intentionally opaque in r2. Phase r3 will bind
    it to laboratory, visit, specialist, source and transfer continuity.
    """

    schema: str
    evidence_ref: str
    evidence_kind: MultiLaboratoryEvidenceKind
    subject_ref: str
    specialist_ref: str
    capability: str
    source_ref: str
    provenance_ref: str
    digest_sha256: str
    claim_key: str
    claim_value: str
    claim_relation: MultiLaboratoryEvidenceClaimRelation
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA:
            raise MultiLaboratoryEvidenceAggregationContractError(
                "unsupported multi-laboratory evidence item schema"
            )
        _require_typed_ref(
            "evidence_ref", self.evidence_ref, _EVIDENCE_PREFIXES
        )
        if self.evidence_kind not in _ALLOWED_EVIDENCE_KINDS:
            raise MultiLaboratoryEvidenceAggregationContractError(
                "unsupported evidence_kind"
            )
        _require_typed_ref("subject_ref", self.subject_ref, _SUBJECT_PREFIXES)
        _require_typed_ref(
            "specialist_ref", self.specialist_ref, _SPECIALIST_PREFIXES
        )
        _require_claim_key("capability", self.capability)
        _require_typed_ref("source_ref", self.source_ref, _SOURCE_PREFIXES)
        _require_typed_ref(
            "provenance_ref", self.provenance_ref, _PROVENANCE_PREFIXES
        )
        if not isinstance(self.digest_sha256, str) or not _SHA256_RE.fullmatch(
            self.digest_sha256
        ):
            raise MultiLaboratoryEvidenceAggregationContractError(
                "digest_sha256 must be a lowercase SHA-256 hexadecimal digest"
            )
        _require_claim_key("claim_key", self.claim_key)
        _require_non_empty("claim_value", self.claim_value)
        if self.claim_relation not in _ALLOWED_CLAIM_RELATIONS:
            raise MultiLaboratoryEvidenceAggregationContractError(
                "unsupported claim_relation"
            )
        object.__setattr__(self, "claim_value", self.claim_value.strip())
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def item_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_item_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(self, *, include_item_digest: bool = True) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "evidence_ref": self.evidence_ref,
            "evidence_kind": self.evidence_kind,
            "subject_ref": self.subject_ref,
            "specialist_ref": self.specialist_ref,
            "capability": self.capability,
            "source_ref": self.source_ref,
            "provenance_ref": self.provenance_ref,
            "digest_sha256": self.digest_sha256,
            "claim_key": self.claim_key,
            "claim_value": self.claim_value,
            "claim_relation": self.claim_relation,
            "metadata": dict(self.metadata),
        }
        if include_item_digest:
            mapping["item_digest"] = self.item_digest
        return mapping


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceAggregate:
    """Canonical immutable aggregation candidate from multiple provenances."""

    schema: str
    aggregation_ref: str
    subject_ref: str
    conversation_ref: str
    context_refs: tuple[str, ...]
    evidence_items: tuple[MultiLaboratoryEvidenceItem, ...]
    aggregation_policy_ref: str
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_AGGREGATE_SCHEMA:
            raise MultiLaboratoryEvidenceAggregationContractError(
                "unsupported multi-laboratory evidence aggregate schema"
            )
        _require_typed_ref(
            "aggregation_ref", self.aggregation_ref, _AGGREGATION_PREFIXES
        )
        _require_typed_ref("subject_ref", self.subject_ref, _SUBJECT_PREFIXES)
        _require_typed_ref(
            "conversation_ref", self.conversation_ref, _CONVERSATION_PREFIXES
        )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs("context_refs", self.context_refs, _CONTEXT_PREFIXES),
        )
        _require_typed_ref(
            "aggregation_policy_ref",
            self.aggregation_policy_ref,
            _POLICY_PREFIXES,
        )

        items = tuple(self.evidence_items)
        if len(items) < 2 or not all(
            isinstance(item, MultiLaboratoryEvidenceItem) for item in items
        ):
            raise MultiLaboratoryEvidenceAggregationContractError(
                "evidence_items must contain at least two evidence items"
            )
        refs = tuple(item.evidence_ref for item in items)
        if len(set(refs)) != len(refs):
            raise MultiLaboratoryEvidenceAggregationContractError(
                "evidence_items must contain unique evidence_ref values"
            )
        if any(item.subject_ref != self.subject_ref for item in items):
            raise MultiLaboratoryEvidenceAggregationContractError(
                "every evidence item must match aggregate subject_ref"
            )
        provenance_refs = {item.provenance_ref for item in items}
        if len(provenance_refs) < 2:
            raise MultiLaboratoryEvidenceAggregationContractError(
                "multi-laboratory candidates require at least two provenance refs"
            )
        object.__setattr__(
            self,
            "evidence_items",
            tuple(sorted(items, key=lambda item: item.evidence_ref)),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def evidence_refs(self) -> tuple[str, ...]:
        return tuple(item.evidence_ref for item in self.evidence_items)

    @property
    def provenance_refs(self) -> tuple[str, ...]:
        return tuple(sorted({item.provenance_ref for item in self.evidence_items}))

    @property
    def content_digests(self) -> tuple[str, ...]:
        """Return all content digests, including duplicates for r4 handling."""
        return tuple(item.digest_sha256 for item in self.evidence_items)

    @property
    def aggregation_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_aggregation_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(
        self, *, include_aggregation_digest: bool = True
    ) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "aggregation_ref": self.aggregation_ref,
            "subject_ref": self.subject_ref,
            "conversation_ref": self.conversation_ref,
            "context_refs": list(self.context_refs),
            "evidence_items": [item.to_mapping() for item in self.evidence_items],
            "aggregation_policy_ref": self.aggregation_policy_ref,
            "metadata": dict(self.metadata),
            "authoritative": False,
            "approved": False,
            "provenance_chain_validated": False,
            "deduplication_performed": False,
            "contradiction_detection_performed": False,
            "weighting_authorized": False,
            "durable_state_written": False,
            "scheduler_selection_allowed": False,
            "laboratory_self_authorization_allowed": False,
            "specialist_self_authorization_allowed": False,
            "qdrant_authoritative": False,
            "github_projects_authoritative": False,
        }
        if include_aggregation_digest:
            mapping["aggregation_digest"] = self.aggregation_digest
        return mapping


def multi_laboratory_evidence_item_from_specialist_capability_evidence_ref(
    evidence: SpecialistCapabilityEvidenceRef,
    *,
    subject_ref: str,
    provenance_ref: str,
    claim_key: str | None = None,
    claim_relation: MultiLaboratoryEvidenceClaimRelation = "supports",
) -> MultiLaboratoryEvidenceItem:
    """Reuse the existing 0285 evidence envelope without redefining it."""

    if not isinstance(evidence, SpecialistCapabilityEvidenceRef):
        raise TypeError("evidence must be SpecialistCapabilityEvidenceRef")
    return MultiLaboratoryEvidenceItem(
        schema=MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA,
        evidence_ref=evidence.evidence_ref,
        evidence_kind=evidence.evidence_kind,
        subject_ref=subject_ref,
        specialist_ref=evidence.specialist_ref,
        capability=evidence.capability,
        source_ref=evidence.source_ref,
        provenance_ref=provenance_ref,
        digest_sha256=evidence.digest_sha256,
        claim_key=claim_key or evidence.capability,
        claim_value=evidence.claim,
        claim_relation=claim_relation,
        metadata=evidence.metadata,
    )


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise MultiLaboratoryEvidenceAggregationContractError(
            f"{name} must be non-empty"
        )


def _require_typed_ref(
    name: str, value: str, prefixes: tuple[str, ...]
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise MultiLaboratoryEvidenceAggregationContractError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(prefixes):
        raise MultiLaboratoryEvidenceAggregationContractError(
            f"{name} must start with one of: {', '.join(prefixes)}"
        )


def _require_claim_key(name: str, value: str) -> None:
    if not isinstance(value, str) or not _CLAIM_KEY_RE.fullmatch(value):
        raise MultiLaboratoryEvidenceAggregationContractError(
            f"{name} must use lowercase dotted identifier syntax"
        )


def _normalize_refs(
    name: str, values: Sequence[str], prefixes: tuple[str, ...]
) -> tuple[str, ...]:
    refs = tuple(values)
    if not refs:
        raise MultiLaboratoryEvidenceAggregationContractError(
            f"{name} must not be empty"
        )
    for value in refs:
        _require_typed_ref(name, value, prefixes)
    return tuple(dict.fromkeys(refs))


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized[key.strip()] = value.strip()
    return tuple(sorted(normalized.items()))


__all__ = (
    "MULTI_LABORATORY_EVIDENCE_AGGREGATE_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_AGGREGATION_CONTRACT_VERSION",
    "MULTI_LABORATORY_EVIDENCE_ITEM_SCHEMA",
    "MultiLaboratoryEvidenceAggregate",
    "MultiLaboratoryEvidenceAggregationContractError",
    "MultiLaboratoryEvidenceClaimRelation",
    "MultiLaboratoryEvidenceItem",
    "MultiLaboratoryEvidenceKind",
    "multi_laboratory_evidence_item_from_specialist_capability_evidence_ref",
)
