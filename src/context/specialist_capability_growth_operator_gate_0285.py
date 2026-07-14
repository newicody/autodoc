"""Explicit operator gate for specialist capability growth, phase 0285-r4.

The gate consumes the immutable r2 proposal and r3 candidate revision contracts.  It
can produce an explicit approve/reject/defer decision, but it performs no durable
write, Scheduler selection, laboratory execution, projection or remote mutation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Literal

from context.portable_specialist_revision_lineage_contract_0285 import (
    PortableSpecialistRevision,
    SpecialistRevisionLineage,
    validate_revision_against_growth_proposal,
)
from context.specialist_capability_growth_proposal_contract_0285 import (
    SpecialistCapabilityGrowthProposal,
)

SPECIALIST_CAPABILITY_GROWTH_DECISION_SCHEMA = (
    "missipy.specialist.capability_growth_decision.v1"
)
SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_SCHEMA = (
    "missipy.specialist.capability_growth_operator_gate.v1"
)
SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_CONTRACT_VERSION = "0285.r4"

SpecialistCapabilityGrowthDecisionOutcome = Literal[
    "approve",
    "reject",
    "defer",
]

_ALLOWED_OUTCOMES = frozenset({"approve", "reject", "defer"})
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
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DECISION_PREFIXES = ("decision:",)
_GATE_PREFIXES = ("gate:",)
_POLICY_PREFIXES = ("policy:",)
_OPERATOR_PREFIXES = ("operator:",)
_PROPOSAL_PREFIXES = ("proposal:",)
_REVISION_PREFIXES = ("revision:",)
_LINEAGE_PREFIXES = ("lineage:",)
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_CONVERSATION_PREFIXES = ("conversation:",)
_CONTEXT_PREFIXES = ("context:", "sql:")


class SpecialistCapabilityGrowthOperatorGateError(ValueError):
    """Raised when an operator decision or gate policy is incoherent."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthDecision:
    """One explicit operator decision bound to a proposal, candidate and policy.

    Approval authorizes the candidate revision for later durable recording.  It does
    not append history, select a runtime revision or dispatch the Scheduler.
    """

    schema: str
    decision_ref: str
    outcome: SpecialistCapabilityGrowthDecisionOutcome
    operator_ref: str
    policy_ref: str
    policy_digest_sha256: str
    proposal_ref: str
    proposal_digest_sha256: str
    candidate_revision_ref: str
    candidate_revision_digest_sha256: str
    base_lineage_ref: str
    base_lineage_digest_sha256: str
    specialist_ref: str
    reason: str
    conversation_ref: str
    context_refs: tuple[str, ...]
    policy_issues: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_DECISION_SCHEMA:
            raise SpecialistCapabilityGrowthOperatorGateError(
                "unsupported specialist capability growth decision schema"
            )
        _require_typed_ref(
            "decision_ref", self.decision_ref, required_prefixes=_DECISION_PREFIXES
        )
        if self.outcome not in _ALLOWED_OUTCOMES:
            raise SpecialistCapabilityGrowthOperatorGateError(
                "outcome must be approve, reject or defer"
            )
        _require_typed_ref(
            "operator_ref", self.operator_ref, required_prefixes=_OPERATOR_PREFIXES
        )
        _require_typed_ref(
            "policy_ref", self.policy_ref, required_prefixes=_POLICY_PREFIXES
        )
        _require_sha256("policy_digest_sha256", self.policy_digest_sha256)
        _require_typed_ref(
            "proposal_ref", self.proposal_ref, required_prefixes=_PROPOSAL_PREFIXES
        )
        _require_sha256("proposal_digest_sha256", self.proposal_digest_sha256)
        _require_typed_ref(
            "candidate_revision_ref",
            self.candidate_revision_ref,
            required_prefixes=_REVISION_PREFIXES,
        )
        _require_sha256(
            "candidate_revision_digest_sha256",
            self.candidate_revision_digest_sha256,
        )
        _require_typed_ref(
            "base_lineage_ref",
            self.base_lineage_ref,
            required_prefixes=_LINEAGE_PREFIXES,
        )
        _require_sha256(
            "base_lineage_digest_sha256", self.base_lineage_digest_sha256
        )
        _require_typed_ref(
            "specialist_ref",
            self.specialist_ref,
            required_prefixes=_SPECIALIST_PREFIXES,
        )
        _require_non_empty("reason", self.reason)
        object.__setattr__(self, "reason", self.reason.strip())
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
        issues = _normalize_strings("policy_issues", self.policy_issues, allow_empty=True)
        if self.outcome == "approve" and issues:
            raise SpecialistCapabilityGrowthOperatorGateError(
                "an approved decision must not contain policy issues"
            )
        object.__setattr__(self, "policy_issues", issues)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def approved(self) -> bool:
        return self.outcome == "approve"

    @property
    def rejected(self) -> bool:
        return self.outcome == "reject"

    @property
    def deferred(self) -> bool:
        return self.outcome == "defer"

    @property
    def revision_authorized(self) -> bool:
        """Whether the candidate may be recorded later as operator-approved."""

        return self.approved and not self.policy_issues

    @property
    def terminal(self) -> bool:
        return self.outcome in {"approve", "reject"}

    @property
    def decision_digest(self) -> str:
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
            "decision_ref": self.decision_ref,
            "outcome": self.outcome,
            "operator_ref": self.operator_ref,
            "policy_ref": self.policy_ref,
            "policy_digest_sha256": self.policy_digest_sha256,
            "proposal_ref": self.proposal_ref,
            "proposal_digest_sha256": self.proposal_digest_sha256,
            "candidate_revision_ref": self.candidate_revision_ref,
            "candidate_revision_digest_sha256": (
                self.candidate_revision_digest_sha256
            ),
            "base_lineage_ref": self.base_lineage_ref,
            "base_lineage_digest_sha256": self.base_lineage_digest_sha256,
            "specialist_ref": self.specialist_ref,
            "reason": self.reason,
            "conversation_ref": self.conversation_ref,
            "context_refs": list(self.context_refs),
            "policy_issues": list(self.policy_issues),
            "metadata": dict(self.metadata),
            "explicit_operator_authority": True,
            "revision_authorized": self.revision_authorized,
            "terminal": self.terminal,
            "durable_state_written": False,
            "scheduler_selection_allowed": False,
            "scheduler_dispatch_performed": False,
            "laboratory_execution_performed": False,
            "qdrant_projection_written": False,
            "eventbus_observation_published": False,
            "github_mutation_performed": False,
        }
        if include_digest:
            mapping["decision_digest"] = self.decision_digest
        return mapping


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthOperatorGate:
    """Pure policy gate producing explicit operator decisions.

    The gate validates one candidate against the current lineage head and the r2
    proposal.  It has no port, adapter, backend or authority to persist or execute the
    result.
    """

    schema: str
    gate_ref: str
    policy_ref: str
    minimum_evidence_count: int = 1
    required_evidence_kinds: tuple[str, ...] = field(default_factory=tuple)
    require_distinct_evidence_sources: bool = False
    allowed_operator_refs: tuple[str, ...] = field(default_factory=tuple)
    require_distinct_operator_from_proposer: bool = False
    allow_deprecate: bool = True
    allow_restore: bool = True
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_SCHEMA:
            raise SpecialistCapabilityGrowthOperatorGateError(
                "unsupported specialist capability growth operator gate schema"
            )
        _require_typed_ref("gate_ref", self.gate_ref, required_prefixes=_GATE_PREFIXES)
        _require_typed_ref(
            "policy_ref", self.policy_ref, required_prefixes=_POLICY_PREFIXES
        )
        if isinstance(self.minimum_evidence_count, bool) or not isinstance(
            self.minimum_evidence_count, int
        ):
            raise SpecialistCapabilityGrowthOperatorGateError(
                "minimum_evidence_count must be an integer"
            )
        if self.minimum_evidence_count < 1:
            raise SpecialistCapabilityGrowthOperatorGateError(
                "minimum_evidence_count must be at least 1"
            )
        evidence_kinds = _normalize_strings(
            "required_evidence_kinds",
            self.required_evidence_kinds,
            allow_empty=True,
        )
        unknown = set(evidence_kinds).difference(_ALLOWED_EVIDENCE_KINDS)
        if unknown:
            raise SpecialistCapabilityGrowthOperatorGateError(
                "required_evidence_kinds contains unsupported values"
            )
        object.__setattr__(self, "required_evidence_kinds", evidence_kinds)
        object.__setattr__(
            self,
            "allowed_operator_refs",
            _normalize_refs(
                "allowed_operator_refs",
                self.allowed_operator_refs,
                required_prefixes=_OPERATOR_PREFIXES,
                allow_empty=True,
            ),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def policy_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def evaluate(
        self,
        proposal: SpecialistCapabilityGrowthProposal,
        candidate_revision: PortableSpecialistRevision,
        base_lineage: SpecialistRevisionLineage,
        *,
        operator_ref: str,
    ) -> tuple[str, ...]:
        """Return deterministic policy issues without mutating any input."""

        _require_gate_inputs(proposal, candidate_revision, base_lineage)
        _require_typed_ref(
            "operator_ref", operator_ref, required_prefixes=_OPERATOR_PREFIXES
        )

        issues = list(
            validate_revision_against_growth_proposal(
                candidate_revision,
                proposal,
                base_lineage.head_revision,
            )
        )
        if candidate_revision.parent_revision_ref != base_lineage.head_revision_ref:
            issues.append("candidate revision must extend the current lineage head")
        if candidate_revision.revision_number != len(base_lineage.revisions) + 1:
            issues.append("candidate revision number must follow the current lineage")
        if candidate_revision.specialist_ref != base_lineage.specialist_ref:
            issues.append("candidate specialist_ref must match base lineage")
        if proposal.specialist_ref != base_lineage.specialist_ref:
            issues.append("proposal specialist_ref must match base lineage")
        if len(proposal.evidence_refs) < self.minimum_evidence_count:
            issues.append("proposal does not satisfy minimum evidence count")

        evidence_kinds = frozenset(item.evidence_kind for item in proposal.evidence_refs)
        missing_kinds = set(self.required_evidence_kinds).difference(evidence_kinds)
        if missing_kinds:
            issues.append(
                "proposal is missing required evidence kinds: "
                + ", ".join(sorted(missing_kinds))
            )
        if self.require_distinct_evidence_sources:
            source_refs = tuple(item.source_ref for item in proposal.evidence_refs)
            if len(set(source_refs)) != len(source_refs):
                issues.append("proposal evidence sources must be distinct")
        if self.allowed_operator_refs and operator_ref not in self.allowed_operator_refs:
            issues.append("operator_ref is not allowed by the gate policy")
        if (
            self.require_distinct_operator_from_proposer
            and operator_ref == proposal.proposer_ref
        ):
            issues.append("operator must be distinct from proposal proposer")
        if proposal.action == "deprecate" and not self.allow_deprecate:
            issues.append("deprecate proposals are disabled by the gate policy")
        if proposal.action == "restore" and not self.allow_restore:
            issues.append("restore proposals are disabled by the gate policy")
        return tuple(dict.fromkeys(issues))

    def decide(
        self,
        proposal: SpecialistCapabilityGrowthProposal,
        candidate_revision: PortableSpecialistRevision,
        base_lineage: SpecialistRevisionLineage,
        *,
        outcome: SpecialistCapabilityGrowthDecisionOutcome,
        decision_ref: str,
        operator_ref: str,
        reason: str,
        metadata: Sequence[tuple[str, str]] = (),
    ) -> SpecialistCapabilityGrowthDecision:
        """Produce one explicit decision; never persist, select or execute it."""

        if outcome not in _ALLOWED_OUTCOMES:
            raise SpecialistCapabilityGrowthOperatorGateError(
                "outcome must be approve, reject or defer"
            )
        issues = self.evaluate(
            proposal,
            candidate_revision,
            base_lineage,
            operator_ref=operator_ref,
        )
        if outcome == "approve" and issues:
            raise SpecialistCapabilityGrowthOperatorGateError(
                "candidate revision cannot be approved: " + "; ".join(issues)
            )
        return SpecialistCapabilityGrowthDecision(
            schema=SPECIALIST_CAPABILITY_GROWTH_DECISION_SCHEMA,
            decision_ref=decision_ref,
            outcome=outcome,
            operator_ref=operator_ref,
            policy_ref=self.policy_ref,
            policy_digest_sha256=self.policy_digest,
            proposal_ref=proposal.proposal_ref,
            proposal_digest_sha256=proposal.proposal_digest,
            candidate_revision_ref=candidate_revision.revision_ref,
            candidate_revision_digest_sha256=candidate_revision.revision_digest,
            base_lineage_ref=base_lineage.lineage_ref,
            base_lineage_digest_sha256=base_lineage.lineage_digest,
            specialist_ref=proposal.specialist_ref,
            reason=reason,
            conversation_ref=proposal.conversation_ref,
            context_refs=proposal.context_refs,
            policy_issues=issues,
            metadata=tuple(metadata),
        )

    def to_mapping(self, *, include_digest: bool = True) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "gate_ref": self.gate_ref,
            "policy_ref": self.policy_ref,
            "minimum_evidence_count": self.minimum_evidence_count,
            "required_evidence_kinds": list(self.required_evidence_kinds),
            "require_distinct_evidence_sources": (
                self.require_distinct_evidence_sources
            ),
            "allowed_operator_refs": list(self.allowed_operator_refs),
            "require_distinct_operator_from_proposer": (
                self.require_distinct_operator_from_proposer
            ),
            "allow_deprecate": self.allow_deprecate,
            "allow_restore": self.allow_restore,
            "metadata": dict(self.metadata),
            "operator_decision_required": True,
            "specialist_self_authorization_allowed": False,
            "laboratory_self_authorization_allowed": False,
            "copilot_self_authorization_allowed": False,
            "scheduler_remains_only_orchestrator": True,
            "durable_state_written": False,
            "runtime_attached": False,
            "network_used": False,
        }
        if include_digest:
            mapping["policy_digest"] = self.policy_digest
        return mapping


def _require_gate_inputs(
    proposal: SpecialistCapabilityGrowthProposal,
    candidate_revision: PortableSpecialistRevision,
    base_lineage: SpecialistRevisionLineage,
) -> None:
    if not isinstance(proposal, SpecialistCapabilityGrowthProposal):
        raise TypeError("proposal must be SpecialistCapabilityGrowthProposal")
    if not isinstance(candidate_revision, PortableSpecialistRevision):
        raise TypeError("candidate_revision must be PortableSpecialistRevision")
    if not isinstance(base_lineage, SpecialistRevisionLineage):
        raise TypeError("base_lineage must be SpecialistRevisionLineage")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SpecialistCapabilityGrowthOperatorGateError(f"{name} must be non-empty")


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefixes: tuple[str, ...],
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthOperatorGateError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(required_prefixes):
        raise SpecialistCapabilityGrowthOperatorGateError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_sha256(name: str, value: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthOperatorGateError(
            f"{name} must be a lowercase SHA-256 digest"
        )


def _normalize_refs(
    name: str,
    refs: Sequence[str],
    *,
    required_prefixes: tuple[str, ...],
    allow_empty: bool = False,
) -> tuple[str, ...]:
    values = tuple(refs)
    if not values and not allow_empty:
        raise SpecialistCapabilityGrowthOperatorGateError(
            f"{name} must not be empty"
        )
    for value in values:
        _require_typed_ref(name, value, required_prefixes=required_prefixes)
    return tuple(dict.fromkeys(values))


def _normalize_strings(
    name: str,
    values: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise SpecialistCapabilityGrowthOperatorGateError(
                f"{name} must contain non-empty strings"
            )
        normalized.append(value.strip())
    if not normalized and not allow_empty:
        raise SpecialistCapabilityGrowthOperatorGateError(
            f"{name} must not be empty"
        )
    return tuple(dict.fromkeys(sorted(normalized)))


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        if not isinstance(key, str) or not key.strip():
            raise SpecialistCapabilityGrowthOperatorGateError(
                "metadata key must be non-empty"
            )
        if not isinstance(value, str) or not value.strip():
            raise SpecialistCapabilityGrowthOperatorGateError(
                "metadata value must be non-empty"
            )
        normalized[key.strip()] = value.strip()
    return tuple(sorted(normalized.items()))


__all__ = (
    "SPECIALIST_CAPABILITY_GROWTH_DECISION_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_CONTRACT_VERSION",
    "SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_SCHEMA",
    "SpecialistCapabilityGrowthDecision",
    "SpecialistCapabilityGrowthDecisionOutcome",
    "SpecialistCapabilityGrowthOperatorGate",
    "SpecialistCapabilityGrowthOperatorGateError",
)
