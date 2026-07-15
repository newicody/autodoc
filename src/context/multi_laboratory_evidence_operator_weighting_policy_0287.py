"""Explicit operator weighting policy for multi-laboratory evidence.

Phase 0287-r6 consumes one valid r5 contradiction-detection proof and produces
an immutable approve/reject/defer decision. Approval authorizes a future r7
history append, but performs no durable write, contradiction resolution,
Scheduler selection, laboratory execution, EventBus publication, Qdrant write
or GitHub mutation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Literal

from context.multi_laboratory_evidence_contradiction_detection_0287 import (
    MultiLaboratoryEvidenceContradiction,
    MultiLaboratoryEvidenceContradictionDetectionResult,
)


MULTI_LABORATORY_EVIDENCE_WEIGHT_SCHEMA = (
    "missipy.multi_laboratory.evidence_weight.v1"
)
MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DISPOSITION_SCHEMA = (
    "missipy.multi_laboratory.evidence_contradiction_disposition.v1"
)
MULTI_LABORATORY_EVIDENCE_WEIGHTING_POLICY_SCHEMA = (
    "missipy.multi_laboratory.evidence_weighting_policy.v1"
)
MULTI_LABORATORY_EVIDENCE_WEIGHTING_DECISION_SCHEMA = (
    "missipy.multi_laboratory.evidence_weighting_decision.v1"
)
MULTI_LABORATORY_EVIDENCE_OPERATOR_WEIGHTING_VERSION = "0287.r6"

MultiLaboratoryEvidenceWeightingOutcome = Literal[
    "approve",
    "reject",
    "defer",
]
MultiLaboratoryEvidenceContradictionAction = Literal[
    "prefer_left",
    "prefer_right",
    "retain_both",
    "exclude_both",
    "defer",
]

_ALLOWED_OUTCOMES = frozenset({"approve", "reject", "defer"})
_ALLOWED_ACTIONS = frozenset(
    {
        "prefer_left",
        "prefer_right",
        "retain_both",
        "exclude_both",
        "defer",
    }
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class MultiLaboratoryEvidenceOperatorWeightingError(ValueError):
    """Raised when an operator weighting decision is incoherent."""


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceWeight:
    """One operator-assigned weight for a canonical evidence reference."""

    schema: str
    canonical_evidence_ref: str
    weight_basis_points: int
    reason: str

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_WEIGHT_SCHEMA:
            raise MultiLaboratoryEvidenceOperatorWeightingError(
                "unsupported evidence weight schema"
            )
        _require_typed_ref(
            "canonical_evidence_ref",
            self.canonical_evidence_ref,
        )
        if (
            isinstance(self.weight_basis_points, bool)
            or not isinstance(self.weight_basis_points, int)
            or not 0 <= self.weight_basis_points <= 10_000
        ):
            raise MultiLaboratoryEvidenceOperatorWeightingError(
                "weight_basis_points must be an integer between 0 and 10000"
            )
        object.__setattr__(self, "reason", _clean_reason(self.reason))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "canonical_evidence_ref": self.canonical_evidence_ref,
            "weight_basis_points": self.weight_basis_points,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceContradictionDisposition:
    """Explicit operator treatment for one still-undurable contradiction."""

    schema: str
    contradiction_ref: str
    action: MultiLaboratoryEvidenceContradictionAction
    reason: str

    def __post_init__(self) -> None:
        if self.schema != (
            MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DISPOSITION_SCHEMA
        ):
            raise MultiLaboratoryEvidenceOperatorWeightingError(
                "unsupported contradiction disposition schema"
            )
        _require_typed_ref("contradiction_ref", self.contradiction_ref)
        if self.action not in _ALLOWED_ACTIONS:
            raise MultiLaboratoryEvidenceOperatorWeightingError(
                "unsupported contradiction disposition action"
            )
        object.__setattr__(self, "reason", _clean_reason(self.reason))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "contradiction_ref": self.contradiction_ref,
            "action": self.action,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceOperatorWeightingPolicy:
    """Pure policy limits for an explicit operator decision."""

    schema: str
    policy_ref: str
    required_total_weight_basis_points: int = 10_000
    allow_zero_weight: bool = True
    require_complete_weight_coverage: bool = True
    require_complete_contradiction_disposition: bool = True

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_WEIGHTING_POLICY_SCHEMA:
            raise MultiLaboratoryEvidenceOperatorWeightingError(
                "unsupported operator weighting policy schema"
            )
        _require_typed_ref("policy_ref", self.policy_ref)
        if (
            isinstance(self.required_total_weight_basis_points, bool)
            or not isinstance(
                self.required_total_weight_basis_points,
                int,
            )
            or not 1 <= self.required_total_weight_basis_points <= 10_000
        ):
            raise MultiLaboratoryEvidenceOperatorWeightingError(
                "required total weight must be between 1 and 10000"
            )

    @property
    def policy_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(
        self,
        *,
        include_digest: bool = True,
    ) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "policy_ref": self.policy_ref,
            "required_total_weight_basis_points": (
                self.required_total_weight_basis_points
            ),
            "allow_zero_weight": self.allow_zero_weight,
            "require_complete_weight_coverage": (
                self.require_complete_weight_coverage
            ),
            "require_complete_contradiction_disposition": (
                self.require_complete_contradiction_disposition
            ),
        }
        if include_digest:
            mapping["policy_digest"] = self.policy_digest
        return mapping


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceWeightingDecision:
    """Immutable operator decision bound to one r5 detection digest."""

    schema: str
    decision_ref: str
    outcome: MultiLaboratoryEvidenceWeightingOutcome
    operator_ref: str
    policy_ref: str
    policy_digest: str
    aggregation_ref: str
    detection_digest: str
    weights: tuple[MultiLaboratoryEvidenceWeight, ...]
    contradiction_dispositions: tuple[
        MultiLaboratoryEvidenceContradictionDisposition, ...
    ]
    canonical_evidence_refs: tuple[str, ...]
    contradiction_refs: tuple[str, ...]
    operator_reviewed_contradiction_refs: tuple[str, ...]
    unresolved_contradiction_refs: tuple[str, ...]
    reason: str
    policy_issues: tuple[str, ...]
    weighting_digest: str
    explicit_operator_authority: bool = field(default=True, init=False)
    durable_state_written: bool = field(default=False, init=False)
    contradiction_resolution_performed: bool = field(
        default=False,
        init=False,
    )
    scheduler_selection_allowed: bool = field(default=False, init=False)
    scheduler_dispatch_performed: bool = field(default=False, init=False)
    laboratory_execution_performed: bool = field(default=False, init=False)
    eventbus_observation_published: bool = field(default=False, init=False)
    qdrant_projection_written: bool = field(default=False, init=False)
    github_mutation_performed: bool = field(default=False, init=False)
    scheduler_remains_only_orchestrator: bool = field(
        default=True,
        init=False,
    )
    sql_remains_durable_authority: bool = field(default=True, init=False)
    laboratory_self_authorization_allowed: bool = field(
        default=False,
        init=False,
    )
    specialist_self_authorization_allowed: bool = field(
        default=False,
        init=False,
    )

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_WEIGHTING_DECISION_SCHEMA:
            raise MultiLaboratoryEvidenceOperatorWeightingError(
                "unsupported weighting decision schema"
            )
        _require_typed_ref("decision_ref", self.decision_ref)
        _require_typed_ref("operator_ref", self.operator_ref)
        _require_typed_ref("policy_ref", self.policy_ref)
        _require_typed_ref("aggregation_ref", self.aggregation_ref)
        _require_sha256("policy_digest", self.policy_digest)
        _require_sha256("detection_digest", self.detection_digest)
        _require_sha256("weighting_digest", self.weighting_digest)
        if self.outcome not in _ALLOWED_OUTCOMES:
            raise MultiLaboratoryEvidenceOperatorWeightingError(
                "outcome must be approve, reject or defer"
            )
        object.__setattr__(self, "reason", _clean_reason(self.reason))
        object.__setattr__(
            self,
            "policy_issues",
            _sorted_unique_strings(self.policy_issues),
        )

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
    def weighting_authorized(self) -> bool:
        return self.approved and not self.policy_issues

    @property
    def durable_history_append_allowed(self) -> bool:
        return self.weighting_authorized

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "decision_ref": self.decision_ref,
            "outcome": self.outcome,
            "operator_ref": self.operator_ref,
            "policy_ref": self.policy_ref,
            "policy_digest": self.policy_digest,
            "aggregation_ref": self.aggregation_ref,
            "detection_digest": self.detection_digest,
            "weights": [item.to_mapping() for item in self.weights],
            "contradiction_dispositions": [
                item.to_mapping()
                for item in self.contradiction_dispositions
            ],
            "canonical_evidence_refs": list(
                self.canonical_evidence_refs
            ),
            "contradiction_refs": list(self.contradiction_refs),
            "operator_reviewed_contradiction_refs": list(
                self.operator_reviewed_contradiction_refs
            ),
            "unresolved_contradiction_refs": list(
                self.unresolved_contradiction_refs
            ),
            "reason": self.reason,
            "policy_issues": list(self.policy_issues),
            "weighting_digest": self.weighting_digest,
            "explicit_operator_authority": True,
            "weighting_authorized": self.weighting_authorized,
            "durable_history_append_allowed": (
                self.durable_history_append_allowed
            ),
            "durable_state_written": False,
            "contradiction_resolution_performed": False,
            "scheduler_selection_allowed": False,
            "scheduler_dispatch_performed": False,
            "laboratory_execution_performed": False,
            "eventbus_observation_published": False,
            "qdrant_projection_written": False,
            "github_mutation_performed": False,
            "scheduler_remains_only_orchestrator": True,
            "sql_remains_durable_authority": True,
            "laboratory_self_authorization_allowed": False,
            "specialist_self_authorization_allowed": False,
        }


def decide_multi_laboratory_evidence_weighting(
    detection: MultiLaboratoryEvidenceContradictionDetectionResult,
    *,
    outcome: MultiLaboratoryEvidenceWeightingOutcome,
    operator_ref: str,
    reason: str,
    weights: Sequence[MultiLaboratoryEvidenceWeight] = (),
    contradiction_dispositions: Sequence[
        MultiLaboratoryEvidenceContradictionDisposition
    ] = (),
    policy: MultiLaboratoryEvidenceOperatorWeightingPolicy | None = None,
    decision_ref: str | None = None,
) -> MultiLaboratoryEvidenceWeightingDecision:
    """Validate and bind one explicit operator weighting decision."""

    if not isinstance(
        detection,
        MultiLaboratoryEvidenceContradictionDetectionResult,
    ):
        raise TypeError(
            "detection must be "
            "MultiLaboratoryEvidenceContradictionDetectionResult"
        )
    if (
        not detection.valid
        or not detection.contradiction_detection_performed
        or not detection.ready_for_operator_weighting
    ):
        raise MultiLaboratoryEvidenceOperatorWeightingError(
            "a valid r5 detection ready for operator weighting is required"
        )
    if outcome not in _ALLOWED_OUTCOMES:
        raise MultiLaboratoryEvidenceOperatorWeightingError(
            "outcome must be approve, reject or defer"
        )
    _require_typed_ref("operator_ref", operator_ref)
    reason_value = _clean_reason(reason)
    policy_value = policy or MultiLaboratoryEvidenceOperatorWeightingPolicy(
        schema=MULTI_LABORATORY_EVIDENCE_WEIGHTING_POLICY_SCHEMA,
        policy_ref="policy:multi-laboratory-weighting-default:v1",
    )

    weight_values = tuple(
        sorted(weights, key=lambda item: item.canonical_evidence_ref)
    )
    disposition_values = tuple(
        sorted(
            contradiction_dispositions,
            key=lambda item: item.contradiction_ref,
        )
    )
    _require_unique_attr(
        "weights",
        weight_values,
        "canonical_evidence_ref",
    )
    _require_unique_attr(
        "contradiction_dispositions",
        disposition_values,
        "contradiction_ref",
    )

    canonical_refs = _canonical_evidence_refs(detection)
    contradiction_refs = tuple(detection.contradiction_refs)
    issues = _policy_issues(
        detection=detection,
        outcome=outcome,
        weights=weight_values,
        dispositions=disposition_values,
        canonical_refs=canonical_refs,
        contradiction_refs=contradiction_refs,
        policy=policy_value,
    )
    if issues:
        raise MultiLaboratoryEvidenceOperatorWeightingError(
            "; ".join(issues)
        )

    reviewed_refs = tuple(
        item.contradiction_ref for item in disposition_values
    )
    unresolved_refs = tuple(detection.unresolved_contradiction_refs)
    payload = {
        "schema": MULTI_LABORATORY_EVIDENCE_WEIGHTING_DECISION_SCHEMA,
        "outcome": outcome,
        "operator_ref": operator_ref,
        "policy_ref": policy_value.policy_ref,
        "policy_digest": policy_value.policy_digest,
        "aggregation_ref": detection.aggregation_ref,
        "detection_digest": detection.detection_digest,
        "weights": [item.to_mapping() for item in weight_values],
        "contradiction_dispositions": [
            item.to_mapping() for item in disposition_values
        ],
        "canonical_evidence_refs": list(canonical_refs),
        "contradiction_refs": list(contradiction_refs),
        "operator_reviewed_contradiction_refs": list(reviewed_refs),
        "unresolved_contradiction_refs": list(unresolved_refs),
        "reason": reason_value,
        "policy_issues": [],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    weighting_digest = sha256(encoded).hexdigest()
    decision_ref_value = (
        decision_ref or f"decision:{weighting_digest}"
    )

    return MultiLaboratoryEvidenceWeightingDecision(
        schema=MULTI_LABORATORY_EVIDENCE_WEIGHTING_DECISION_SCHEMA,
        decision_ref=decision_ref_value,
        outcome=outcome,
        operator_ref=operator_ref,
        policy_ref=policy_value.policy_ref,
        policy_digest=policy_value.policy_digest,
        aggregation_ref=detection.aggregation_ref,
        detection_digest=detection.detection_digest,
        weights=weight_values,
        contradiction_dispositions=disposition_values,
        canonical_evidence_refs=canonical_refs,
        contradiction_refs=contradiction_refs,
        operator_reviewed_contradiction_refs=reviewed_refs,
        unresolved_contradiction_refs=unresolved_refs,
        reason=reason_value,
        policy_issues=(),
        weighting_digest=weighting_digest,
    )


def _policy_issues(
    *,
    detection: MultiLaboratoryEvidenceContradictionDetectionResult,
    outcome: MultiLaboratoryEvidenceWeightingOutcome,
    weights: tuple[MultiLaboratoryEvidenceWeight, ...],
    dispositions: tuple[
        MultiLaboratoryEvidenceContradictionDisposition, ...
    ],
    canonical_refs: tuple[str, ...],
    contradiction_refs: tuple[str, ...],
    policy: MultiLaboratoryEvidenceOperatorWeightingPolicy,
) -> tuple[str, ...]:
    issues: list[str] = []
    weight_refs = tuple(
        item.canonical_evidence_ref for item in weights
    )
    disposition_refs = tuple(
        item.contradiction_ref for item in dispositions
    )

    if outcome == "approve":
        if (
            policy.require_complete_weight_coverage
            and weight_refs != canonical_refs
        ):
            issues.append(
                "approve requires one weight for every canonical evidence ref"
            )
        if sum(item.weight_basis_points for item in weights) != (
            policy.required_total_weight_basis_points
        ):
            issues.append(
                "approved weights must match the policy total"
            )
        if (
            not policy.allow_zero_weight
            and any(item.weight_basis_points == 0 for item in weights)
        ):
            issues.append("zero weights are forbidden by policy")
        if (
            policy.require_complete_contradiction_disposition
            and disposition_refs != contradiction_refs
        ):
            issues.append(
                "approve requires one disposition for every contradiction"
            )
        if any(item.action == "defer" for item in dispositions):
            issues.append(
                "approved contradiction dispositions cannot defer"
            )
        issues.extend(
            _contradiction_weight_issues(
                detection.contradictions,
                weights,
                dispositions,
            )
        )
    elif outcome == "reject":
        if weights or dispositions:
            issues.append(
                "reject must not authorize weights or dispositions"
            )
    elif outcome == "defer":
        if weights:
            issues.append("defer must not assign evidence weights")
        if contradiction_refs:
            if disposition_refs != contradiction_refs:
                issues.append(
                    "defer requires one disposition for every contradiction"
                )
            if any(item.action != "defer" for item in dispositions):
                issues.append(
                    "deferred contradiction dispositions must use defer"
                )
        elif dispositions:
            issues.append(
                "contradiction-free defer must not contain dispositions"
            )

    return tuple(sorted(set(issues)))


def _contradiction_weight_issues(
    contradictions: Sequence[MultiLaboratoryEvidenceContradiction],
    weights: Sequence[MultiLaboratoryEvidenceWeight],
    dispositions: Sequence[
        MultiLaboratoryEvidenceContradictionDisposition
    ],
) -> tuple[str, ...]:
    weight_by_ref = {
        item.canonical_evidence_ref: item.weight_basis_points
        for item in weights
    }
    disposition_by_ref = {
        item.contradiction_ref: item
        for item in dispositions
    }
    issues: list[str] = []

    for contradiction in contradictions:
        disposition = disposition_by_ref.get(
            contradiction.contradiction_ref
        )
        if disposition is None:
            continue
        left_ref = contradiction.left_canonical_evidence_ref
        right_ref = contradiction.right_canonical_evidence_ref
        left_weight = weight_by_ref.get(left_ref)
        right_weight = weight_by_ref.get(right_ref)
        if left_weight is None or right_weight is None:
            continue

        if left_ref == right_ref and disposition.action in {
            "prefer_left",
            "prefer_right",
        }:
            issues.append(
                "same-canonical contradiction cannot prefer one side"
            )
        elif (
            disposition.action == "prefer_left"
            and left_weight <= right_weight
        ):
            issues.append(
                "prefer_left requires a greater left canonical weight"
            )
        elif (
            disposition.action == "prefer_right"
            and right_weight <= left_weight
        ):
            issues.append(
                "prefer_right requires a greater right canonical weight"
            )
        elif (
            disposition.action == "retain_both"
            and (left_weight == 0 or right_weight == 0)
        ):
            issues.append(
                "retain_both requires non-zero weights on both sides"
            )
        elif (
            disposition.action == "exclude_both"
            and (left_weight != 0 or right_weight != 0)
        ):
            issues.append(
                "exclude_both requires zero weights on both sides"
            )

    return tuple(issues)


def _canonical_evidence_refs(
    detection: MultiLaboratoryEvidenceContradictionDetectionResult,
) -> tuple[str, ...]:
    refs = set(detection.unaffected_canonical_evidence_refs)
    for contradiction in detection.contradictions:
        refs.add(contradiction.left_canonical_evidence_ref)
        refs.add(contradiction.right_canonical_evidence_ref)
    return tuple(sorted(refs))


def _require_unique_attr(
    name: str,
    values: Sequence[object],
    attribute: str,
) -> None:
    refs = tuple(getattr(item, attribute) for item in values)
    if len(refs) != len(set(refs)):
        raise MultiLaboratoryEvidenceOperatorWeightingError(
            f"{name} must contain unique {attribute} values"
        )


def _require_typed_ref(name: str, value: str) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise MultiLaboratoryEvidenceOperatorWeightingError(
            f"{name} must be a typed reference"
        )


def _require_sha256(name: str, value: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise MultiLaboratoryEvidenceOperatorWeightingError(
            f"{name} must be a lowercase SHA-256"
        )


def _clean_reason(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MultiLaboratoryEvidenceOperatorWeightingError(
            "reason must be non-empty"
        )
    return " ".join(value.split())


def _sorted_unique_strings(
    values: Sequence[str],
) -> tuple[str, ...]:
    result = tuple(sorted(values))
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise MultiLaboratoryEvidenceOperatorWeightingError(
            "policy_issues must contain non-empty strings"
        )
    if len(result) != len(set(result)):
        raise MultiLaboratoryEvidenceOperatorWeightingError(
            "policy_issues must be unique"
        )
    return result


__all__ = (
    "MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DISPOSITION_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_OPERATOR_WEIGHTING_VERSION",
    "MULTI_LABORATORY_EVIDENCE_WEIGHTING_DECISION_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_WEIGHTING_POLICY_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_WEIGHT_SCHEMA",
    "MultiLaboratoryEvidenceContradictionAction",
    "MultiLaboratoryEvidenceContradictionDisposition",
    "MultiLaboratoryEvidenceOperatorWeightingError",
    "MultiLaboratoryEvidenceOperatorWeightingPolicy",
    "MultiLaboratoryEvidenceWeight",
    "MultiLaboratoryEvidenceWeightingDecision",
    "MultiLaboratoryEvidenceWeightingOutcome",
    "decide_multi_laboratory_evidence_weighting",
)
