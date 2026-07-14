"""Immutable, evidence-backed capability-growth proposal contracts for phase 0285-r2.

This module is deliberately declarative.  It does not approve a proposal, mutate a
specialist descriptor, select a runtime, write durable state, or dispatch work.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Literal

SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA = (
    "missipy.specialist.capability_evidence_ref.v1"
)
SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA = (
    "missipy.specialist.capability_growth_proposal.v1"
)
SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_CONTRACT_VERSION = "0285.r2"

SpecialistCapabilityEvidenceKind = Literal[
    "artifact",
    "benchmark",
    "execution_result",
    "observation",
    "operator_review",
    "test_report",
]
SpecialistCapabilityGrowthAction = Literal[
    "add",
    "refine",
    "deprecate",
    "restore",
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
_ALLOWED_GROWTH_ACTIONS = frozenset({"add", "refine", "deprecate", "restore"})
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_.-]+$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}(?:[-+][a-z0-9.-]+)?$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_PROPOSAL_PREFIXES = ("proposal:",)
_EVIDENCE_PREFIXES = (
    "artifact:",
    "evidence:",
    "observation:",
    "report:",
    "result:",
    "sql:",
    "test:",
)
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
_PROPOSER_PREFIXES = (
    "actor:",
    "copilot:",
    "laboratory:",
    "operator:",
    "specialist:",
    "system:",
)
_CONVERSATION_PREFIXES = ("conversation:",)
_CONTEXT_PREFIXES = ("context:", "sql:")
_CONTRACT_PREFIXES = ("contract:",)
_LABORATORY_CAPABILITY_PREFIXES = ("laboratory-capability:",)


class SpecialistCapabilityGrowthProposalContractError(ValueError):
    """Raised when an immutable capability-growth proposal is incoherent."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityEvidenceRef:
    """Digest-bound evidence reference supporting one specialist capability claim."""

    schema: str
    evidence_ref: str
    evidence_kind: SpecialistCapabilityEvidenceKind
    specialist_ref: str
    capability: str
    source_ref: str
    digest_sha256: str
    claim: str
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA:
            raise SpecialistCapabilityGrowthProposalContractError(
                "unsupported specialist capability evidence schema"
            )
        _require_typed_ref(
            "evidence_ref", self.evidence_ref, required_prefixes=_EVIDENCE_PREFIXES
        )
        if self.evidence_kind not in _ALLOWED_EVIDENCE_KINDS:
            raise SpecialistCapabilityGrowthProposalContractError(
                "unsupported specialist capability evidence kind"
            )
        _require_typed_ref(
            "specialist_ref", self.specialist_ref, required_prefixes=_SPECIALIST_PREFIXES
        )
        _require_capability(self.capability)
        _require_typed_ref("source_ref", self.source_ref, required_prefixes=_SOURCE_PREFIXES)
        if not isinstance(self.digest_sha256, str) or not _SHA256_RE.fullmatch(
            self.digest_sha256
        ):
            raise SpecialistCapabilityGrowthProposalContractError(
                "digest_sha256 must be a lowercase SHA-256 hexadecimal digest"
            )
        _require_non_empty("claim", self.claim)
        object.__setattr__(self, "claim", self.claim.strip())
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "evidence_ref": self.evidence_ref,
            "evidence_kind": self.evidence_kind,
            "specialist_ref": self.specialist_ref,
            "capability": self.capability,
            "source_ref": self.source_ref,
            "digest_sha256": self.digest_sha256,
            "claim": self.claim,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProposal:
    """Non-authoritative proposal to change one capability of a stable specialist."""

    schema: str
    proposal_ref: str
    specialist_ref: str
    base_specialist_version: str
    action: SpecialistCapabilityGrowthAction
    capability: str
    proposed_description: str
    evidence_refs: tuple[SpecialistCapabilityEvidenceRef, ...]
    proposer_ref: str
    conversation_ref: str
    context_refs: tuple[str, ...]
    requested_input_contract_refs: tuple[str, ...] = field(default_factory=tuple)
    requested_output_contract_refs: tuple[str, ...] = field(default_factory=tuple)
    requested_laboratory_capability_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA:
            raise SpecialistCapabilityGrowthProposalContractError(
                "unsupported specialist capability growth proposal schema"
            )
        _require_typed_ref(
            "proposal_ref", self.proposal_ref, required_prefixes=_PROPOSAL_PREFIXES
        )
        _require_typed_ref(
            "specialist_ref", self.specialist_ref, required_prefixes=_SPECIALIST_PREFIXES
        )
        if not isinstance(self.base_specialist_version, str) or not _VERSION_RE.fullmatch(
            self.base_specialist_version
        ):
            raise SpecialistCapabilityGrowthProposalContractError(
                "base_specialist_version must be a dotted numeric version"
            )
        if self.action not in _ALLOWED_GROWTH_ACTIONS:
            raise SpecialistCapabilityGrowthProposalContractError(
                "unsupported specialist capability growth action"
            )
        _require_capability(self.capability)
        _require_non_empty("proposed_description", self.proposed_description)
        object.__setattr__(
            self, "proposed_description", self.proposed_description.strip()
        )

        evidence_refs = tuple(self.evidence_refs)
        if not evidence_refs or not all(
            isinstance(item, SpecialistCapabilityEvidenceRef) for item in evidence_refs
        ):
            raise SpecialistCapabilityGrowthProposalContractError(
                "evidence_refs must contain SpecialistCapabilityEvidenceRef values"
            )
        evidence_ids = tuple(item.evidence_ref for item in evidence_refs)
        if len(set(evidence_ids)) != len(evidence_ids):
            raise SpecialistCapabilityGrowthProposalContractError(
                "evidence_refs must contain unique evidence_ref values"
            )
        for evidence in evidence_refs:
            if evidence.specialist_ref != self.specialist_ref:
                raise SpecialistCapabilityGrowthProposalContractError(
                    "evidence specialist_ref must match proposal specialist_ref"
                )
            if evidence.capability != self.capability:
                raise SpecialistCapabilityGrowthProposalContractError(
                    "evidence capability must match proposal capability"
                )
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(sorted(evidence_refs, key=lambda item: item.evidence_ref)),
        )

        _require_typed_ref(
            "proposer_ref", self.proposer_ref, required_prefixes=_PROPOSER_PREFIXES
        )
        _require_typed_ref(
            "conversation_ref",
            self.conversation_ref,
            required_prefixes=_CONVERSATION_PREFIXES,
        )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs(
                "context_refs", self.context_refs, required_prefixes=_CONTEXT_PREFIXES
            ),
        )

        input_refs = _normalize_refs(
            "requested_input_contract_refs",
            self.requested_input_contract_refs,
            allow_empty=self.action == "deprecate",
            required_prefixes=_CONTRACT_PREFIXES,
        )
        output_refs = _normalize_refs(
            "requested_output_contract_refs",
            self.requested_output_contract_refs,
            allow_empty=self.action == "deprecate",
            required_prefixes=_CONTRACT_PREFIXES,
        )
        if self.action != "deprecate" and (not input_refs or not output_refs):
            raise SpecialistCapabilityGrowthProposalContractError(
                "non-deprecation proposals require input and output contract refs"
            )
        object.__setattr__(self, "requested_input_contract_refs", input_refs)
        object.__setattr__(self, "requested_output_contract_refs", output_refs)
        object.__setattr__(
            self,
            "requested_laboratory_capability_refs",
            _normalize_refs(
                "requested_laboratory_capability_refs",
                self.requested_laboratory_capability_refs,
                allow_empty=True,
                required_prefixes=_LABORATORY_CAPABILITY_PREFIXES,
            ),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def proposal_digest(self) -> str:
        """Return the deterministic digest of the complete proposal projection."""

        payload = json.dumps(
            self.to_mapping(include_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(self, *, include_digest: bool = True) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "proposal_ref": self.proposal_ref,
            "specialist_ref": self.specialist_ref,
            "base_specialist_version": self.base_specialist_version,
            "action": self.action,
            "capability": self.capability,
            "proposed_description": self.proposed_description,
            "evidence_refs": [item.to_mapping() for item in self.evidence_refs],
            "proposer_ref": self.proposer_ref,
            "conversation_ref": self.conversation_ref,
            "context_refs": list(self.context_refs),
            "requested_input_contract_refs": list(
                self.requested_input_contract_refs
            ),
            "requested_output_contract_refs": list(
                self.requested_output_contract_refs
            ),
            "requested_laboratory_capability_refs": list(
                self.requested_laboratory_capability_refs
            ),
            "metadata": dict(self.metadata),
            "authoritative": False,
            "approved": False,
            "scheduler_dispatch_allowed": False,
            "specialist_self_authorization_allowed": False,
            "laboratory_self_authorization_allowed": False,
            "copilot_self_authorization_allowed": False,
            "descriptor_mutated": False,
            "durable_state_written": False,
        }
        if include_digest:
            mapping["proposal_digest"] = self.proposal_digest
        return mapping


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SpecialistCapabilityGrowthProposalContractError(
            f"{name} must be non-empty"
        )


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefixes: tuple[str, ...],
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthProposalContractError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(required_prefixes):
        raise SpecialistCapabilityGrowthProposalContractError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_capability(value: str) -> None:
    if not isinstance(value, str) or not _CAPABILITY_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthProposalContractError(
            "capability must use lowercase dotted identifier syntax"
        )


def _normalize_refs(
    name: str,
    refs: Sequence[str],
    *,
    allow_empty: bool = False,
    required_prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    values = tuple(refs)
    if not values and not allow_empty:
        raise SpecialistCapabilityGrowthProposalContractError(
            f"{name} must not be empty"
        )
    for ref in values:
        _require_typed_ref(name, ref, required_prefixes=required_prefixes)
    return tuple(dict.fromkeys(values))


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
    "SPECIALIST_CAPABILITY_EVIDENCE_REF_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_CONTRACT_VERSION",
    "SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_SCHEMA",
    "SpecialistCapabilityEvidenceKind",
    "SpecialistCapabilityEvidenceRef",
    "SpecialistCapabilityGrowthAction",
    "SpecialistCapabilityGrowthProposal",
    "SpecialistCapabilityGrowthProposalContractError",
)
