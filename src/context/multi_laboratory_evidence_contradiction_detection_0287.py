"""Explicit contradiction detection for multi-laboratory evidence.

Phase 0287-r5 consumes the valid r4 deduplication proof. It detects only
bounded, explainable incompatibilities:

* the same claim value is both supported and opposed;
* a policy declares two values mutually exclusive;
* a policy declares a claim key single-valued and positive evidence supports
  different values;
* one content digest carries incompatible interpretations of the same claim.

Every contradiction stays unresolved. Laboratories and specialists cannot
resolve or weight their own evidence. Operator weighting remains phase r6.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from itertools import combinations
import json
import re
from typing import Literal

from context.multi_laboratory_evidence_aggregation_contract_0287 import (
    MultiLaboratoryEvidenceItem,
)
from context.multi_laboratory_evidence_digest_deduplication_0287 import (
    MultiLaboratoryEvidenceDeduplicationResult,
    MultiLaboratoryEvidenceDigestGroup,
)


MULTI_LABORATORY_EVIDENCE_CONTRADICTION_POLICY_SCHEMA = (
    "missipy.multi_laboratory.evidence_contradiction_policy.v1"
)
MULTI_LABORATORY_EVIDENCE_CONTRADICTION_SCHEMA = (
    "missipy.multi_laboratory.evidence_contradiction.v1"
)
MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_SCHEMA = (
    "missipy.multi_laboratory.evidence_contradiction_detection.v1"
)
MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_VERSION = "0287.r5"

MultiLaboratoryEvidenceContradictionKind = Literal[
    "relation_opposition",
    "exclusive_value_conflict",
    "same_content_claim_variant",
]

_ALLOWED_KINDS = frozenset(
    {
        "relation_opposition",
        "exclusive_value_conflict",
        "same_content_claim_variant",
    }
)
_POSITIVE_RELATIONS = frozenset({"supports", "observes", "measures"})
_CLAIM_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]+$")
_POLICY_REF_RE = re.compile(r"^policy:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class MultiLaboratoryEvidenceContradictionDetectionError(ValueError):
    """Raised when a contradiction policy or proof is incoherent."""


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceContradictionPolicy:
    """Explicit policy for bounded contradiction semantics."""

    schema: str
    policy_ref: str
    exclusive_claim_keys: tuple[str, ...] = field(default_factory=tuple)
    exclusive_value_pairs: tuple[tuple[str, str, str], ...] = field(
        default_factory=tuple
    )
    detect_relation_opposition: bool = True
    detect_same_content_claim_variants: bool = True

    def __post_init__(self) -> None:
        if self.schema != (
            MULTI_LABORATORY_EVIDENCE_CONTRADICTION_POLICY_SCHEMA
        ):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "unsupported contradiction policy schema"
            )
        if not isinstance(self.policy_ref, str) or not _POLICY_REF_RE.fullmatch(
            self.policy_ref
        ):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "policy_ref must start with policy:"
            )
        keys = tuple(sorted(self.exclusive_claim_keys))
        if len(keys) != len(set(keys)):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "exclusive_claim_keys must be unique"
            )
        for key in keys:
            _require_claim_key(key)

        normalized_pairs: list[tuple[str, str, str]] = []
        for raw in self.exclusive_value_pairs:
            if not isinstance(raw, tuple) or len(raw) != 3:
                raise MultiLaboratoryEvidenceContradictionDetectionError(
                    "exclusive_value_pairs must contain "
                    "(claim_key, left_value, right_value)"
                )
            claim_key, left_value, right_value = raw
            _require_claim_key(claim_key)
            left = _normalize_claim_value(left_value)
            right = _normalize_claim_value(right_value)
            if left == right:
                raise MultiLaboratoryEvidenceContradictionDetectionError(
                    "exclusive values must differ"
                )
            normalized_pairs.append(
                (claim_key, *sorted((left, right)))
            )
        pairs = tuple(sorted(set(normalized_pairs)))
        if len(pairs) != len(normalized_pairs):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "exclusive_value_pairs must be unique"
            )
        object.__setattr__(self, "exclusive_claim_keys", keys)
        object.__setattr__(self, "exclusive_value_pairs", pairs)

    @property
    def policy_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_policy_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(
        self,
        *,
        include_policy_digest: bool = True,
    ) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "policy_ref": self.policy_ref,
            "exclusive_claim_keys": list(self.exclusive_claim_keys),
            "exclusive_value_pairs": [
                {
                    "claim_key": claim_key,
                    "left_value": left_value,
                    "right_value": right_value,
                }
                for claim_key, left_value, right_value
                in self.exclusive_value_pairs
            ],
            "detect_relation_opposition": self.detect_relation_opposition,
            "detect_same_content_claim_variants": (
                self.detect_same_content_claim_variants
            ),
        }
        if include_policy_digest:
            mapping["policy_digest"] = self.policy_digest
        return mapping


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceContradiction:
    """One deterministic, still-unresolved incompatibility."""

    schema: str
    contradiction_ref: str
    contradiction_kind: MultiLaboratoryEvidenceContradictionKind
    claim_key: str
    left_evidence_ref: str
    right_evidence_ref: str
    left_canonical_evidence_ref: str
    right_canonical_evidence_ref: str
    left_claim_value: str
    right_claim_value: str
    left_claim_relation: str
    right_claim_relation: str
    content_digests: tuple[str, ...]
    source_refs: tuple[str, ...]
    laboratory_refs: tuple[str, ...]
    specialist_refs: tuple[str, ...]
    resolution_state: str = "unresolved"

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_CONTRADICTION_SCHEMA:
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "unsupported contradiction schema"
            )
        if self.contradiction_kind not in _ALLOWED_KINDS:
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "unsupported contradiction_kind"
            )
        _require_claim_key(self.claim_key)
        if not self.contradiction_ref.startswith("contradiction:"):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "contradiction_ref must start with contradiction:"
            )
        digest = self.contradiction_ref.removeprefix("contradiction:")
        if not _SHA256_RE.fullmatch(digest):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "contradiction_ref must contain a SHA-256"
            )
        if self.left_evidence_ref >= self.right_evidence_ref:
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "evidence refs must use deterministic sorted order"
            )
        if self.resolution_state != "unresolved":
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "r5 contradictions must remain unresolved"
            )
        object.__setattr__(
            self,
            "content_digests",
            _sorted_unique(
                "content_digests",
                self.content_digests,
                require_non_empty=True,
                sha256_values=True,
            ),
        )
        object.__setattr__(
            self,
            "source_refs",
            _sorted_unique(
                "source_refs",
                self.source_refs,
                require_non_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "laboratory_refs",
            _sorted_unique(
                "laboratory_refs",
                self.laboratory_refs,
                require_non_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "specialist_refs",
            _sorted_unique(
                "specialist_refs",
                self.specialist_refs,
                require_non_empty=True,
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "contradiction_ref": self.contradiction_ref,
            "contradiction_kind": self.contradiction_kind,
            "claim_key": self.claim_key,
            "left_evidence_ref": self.left_evidence_ref,
            "right_evidence_ref": self.right_evidence_ref,
            "left_canonical_evidence_ref": (
                self.left_canonical_evidence_ref
            ),
            "right_canonical_evidence_ref": (
                self.right_canonical_evidence_ref
            ),
            "left_claim_value": self.left_claim_value,
            "right_claim_value": self.right_claim_value,
            "left_claim_relation": self.left_claim_relation,
            "right_claim_relation": self.right_claim_relation,
            "content_digests": list(self.content_digests),
            "source_refs": list(self.source_refs),
            "laboratory_refs": list(self.laboratory_refs),
            "specialist_refs": list(self.specialist_refs),
            "resolution_state": "unresolved",
        }


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceContradictionDetectionResult:
    """Immutable r5 detection proof; resolution and weighting stay in r6."""

    schema: str
    valid: bool
    issues: tuple[str, ...]
    aggregation_ref: str
    aggregation_digest: str
    deduplication_digest: str
    policy_ref: str
    policy_digest: str
    contradictions: tuple[MultiLaboratoryEvidenceContradiction, ...]
    contradiction_refs: tuple[str, ...]
    unresolved_contradictions: tuple[
        MultiLaboratoryEvidenceContradiction, ...
    ]
    unresolved_contradiction_refs: tuple[str, ...]
    evidence_refs_with_contradictions: tuple[str, ...]
    unaffected_canonical_evidence_refs: tuple[str, ...]
    contradiction_count: int
    unresolved_contradiction_count: int
    contradiction_free: bool
    contradiction_detection_performed: bool
    ready_for_operator_weighting: bool
    detection_digest: str
    authoritative: bool = field(default=False, init=False)
    approved: bool = field(default=False, init=False)
    provenance_chain_validated: bool = field(default=True, init=False)
    deduplication_performed: bool = field(default=True, init=False)
    weighting_authorized: bool = field(default=False, init=False)
    durable_state_written: bool = field(default=False, init=False)
    scheduler_selection_allowed: bool = field(default=False, init=False)
    laboratory_self_authorization_allowed: bool = field(
        default=False,
        init=False,
    )
    specialist_self_authorization_allowed: bool = field(
        default=False,
        init=False,
    )
    sql_remains_durable_authority: bool = field(default=True, init=False)
    scheduler_remains_only_orchestrator: bool = field(
        default=True,
        init=False,
    )
    qdrant_authoritative: bool = field(default=False, init=False)
    github_projects_authoritative: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != (
            MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_SCHEMA
        ):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "unsupported contradiction detection schema"
            )
        for name, value in (
            ("aggregation_digest", self.aggregation_digest),
            ("deduplication_digest", self.deduplication_digest),
            ("policy_digest", self.policy_digest),
            ("detection_digest", self.detection_digest),
        ):
            if not _SHA256_RE.fullmatch(value):
                raise MultiLaboratoryEvidenceContradictionDetectionError(
                    f"{name} must be a lowercase SHA-256"
                )
        issues = tuple(self.issues)
        contradictions = tuple(self.contradictions)
        unresolved = tuple(self.unresolved_contradictions)
        refs = tuple(item.contradiction_ref for item in contradictions)
        unresolved_refs = tuple(
            item.contradiction_ref for item in unresolved
        )
        if self.valid != (
            not issues
            and self.contradiction_detection_performed
            and self.ready_for_operator_weighting
        ):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "valid flag does not match detection state"
            )
        if refs != self.contradiction_refs:
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "contradiction_refs do not match contradictions"
            )
        if unresolved != contradictions:
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "all r5 contradictions must remain unresolved"
            )
        if unresolved_refs != self.unresolved_contradiction_refs:
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "unresolved contradiction refs do not match"
            )
        if self.contradiction_count != len(contradictions):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "contradiction_count does not match contradictions"
            )
        if self.unresolved_contradiction_count != len(unresolved):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "unresolved_contradiction_count does not match"
            )
        if self.contradiction_free != (not contradictions):
            raise MultiLaboratoryEvidenceContradictionDetectionError(
                "contradiction_free does not match contradictions"
            )
        object.__setattr__(self, "issues", issues)
        object.__setattr__(self, "contradictions", contradictions)
        object.__setattr__(
            self,
            "unresolved_contradictions",
            unresolved,
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "aggregation_ref": self.aggregation_ref,
            "aggregation_digest": self.aggregation_digest,
            "deduplication_digest": self.deduplication_digest,
            "policy_ref": self.policy_ref,
            "policy_digest": self.policy_digest,
            "contradictions": [
                item.to_mapping() for item in self.contradictions
            ],
            "contradiction_refs": list(self.contradiction_refs),
            "unresolved_contradictions": [
                item.to_mapping()
                for item in self.unresolved_contradictions
            ],
            "unresolved_contradiction_refs": list(
                self.unresolved_contradiction_refs
            ),
            "evidence_refs_with_contradictions": list(
                self.evidence_refs_with_contradictions
            ),
            "unaffected_canonical_evidence_refs": list(
                self.unaffected_canonical_evidence_refs
            ),
            "contradiction_count": self.contradiction_count,
            "unresolved_contradiction_count": (
                self.unresolved_contradiction_count
            ),
            "contradiction_free": self.contradiction_free,
            "contradiction_detection_performed": (
                self.contradiction_detection_performed
            ),
            "ready_for_operator_weighting": (
                self.ready_for_operator_weighting
            ),
            "detection_digest": self.detection_digest,
            "authoritative": False,
            "approved": False,
            "provenance_chain_validated": self.valid,
            "deduplication_performed": self.valid,
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


def detect_multi_laboratory_evidence_contradictions(
    deduplication: MultiLaboratoryEvidenceDeduplicationResult,
    policy: MultiLaboratoryEvidenceContradictionPolicy | None = None,
) -> MultiLaboratoryEvidenceContradictionDetectionResult:
    """Detect explicit contradictions without resolving or weighting them."""

    if not isinstance(
        deduplication,
        MultiLaboratoryEvidenceDeduplicationResult,
    ):
        raise TypeError(
            "deduplication must be MultiLaboratoryEvidenceDeduplicationResult"
        )
    policy_value = policy or MultiLaboratoryEvidenceContradictionPolicy(
        schema=MULTI_LABORATORY_EVIDENCE_CONTRADICTION_POLICY_SCHEMA,
        policy_ref="policy:multi-laboratory-contradiction-default:v1",
    )
    if not isinstance(
        policy_value,
        MultiLaboratoryEvidenceContradictionPolicy,
    ):
        raise TypeError(
            "policy must be MultiLaboratoryEvidenceContradictionPolicy"
        )

    if not deduplication.valid or not deduplication.deduplication_performed:
        issues = (
            "valid r4 deduplication is required before contradiction detection",
        )
        return _result(
            deduplication=deduplication,
            policy=policy_value,
            contradictions=(),
            issues=issues,
            performed=False,
        )

    items = tuple(
        sorted(
            deduplication.retained_evidence_items,
            key=lambda item: item.evidence_ref,
        )
    )
    canonical_by_ref = {
        ref: ref for ref in deduplication.canonical_evidence_refs
    }
    canonical_by_ref.update(
        {
            duplicate_ref: canonical_ref
            for duplicate_ref, canonical_ref
            in deduplication.evidence_aliases
        }
    )
    groups_by_digest = {
        group.digest_sha256: group
        for group in deduplication.digest_groups
    }

    contradictions: list[MultiLaboratoryEvidenceContradiction] = []
    already_detected_pairs: set[tuple[str, str]] = set()

    for left, right in combinations(items, 2):
        pair = (left.evidence_ref, right.evidence_ref)
        kind = _contradiction_kind(left, right, policy_value)
        if kind is None:
            continue
        contradiction = _build_contradiction(
            kind=kind,
            left=left,
            right=right,
            canonical_by_ref=canonical_by_ref,
            groups_by_digest=groups_by_digest,
            policy_digest=policy_value.policy_digest,
        )
        contradictions.append(contradiction)
        already_detected_pairs.add(pair)

    if policy_value.detect_same_content_claim_variants:
        for left, right in combinations(items, 2):
            pair = (left.evidence_ref, right.evidence_ref)
            if pair in already_detected_pairs:
                continue
            if (
                left.digest_sha256 == right.digest_sha256
                and left.claim_key == right.claim_key
                and (
                    _normalize_claim_value(left.claim_value)
                    != _normalize_claim_value(right.claim_value)
                    or left.claim_relation != right.claim_relation
                )
            ):
                contradictions.append(
                    _build_contradiction(
                        kind="same_content_claim_variant",
                        left=left,
                        right=right,
                        canonical_by_ref=canonical_by_ref,
                        groups_by_digest=groups_by_digest,
                        policy_digest=policy_value.policy_digest,
                    )
                )

    contradiction_values = tuple(
        sorted(
            contradictions,
            key=lambda item: item.contradiction_ref,
        )
    )
    return _result(
        deduplication=deduplication,
        policy=policy_value,
        contradictions=contradiction_values,
        issues=(),
        performed=True,
    )


def _contradiction_kind(
    left: MultiLaboratoryEvidenceItem,
    right: MultiLaboratoryEvidenceItem,
    policy: MultiLaboratoryEvidenceContradictionPolicy,
) -> MultiLaboratoryEvidenceContradictionKind | None:
    if left.claim_key != right.claim_key:
        return None

    left_value = _normalize_claim_value(left.claim_value)
    right_value = _normalize_claim_value(right.claim_value)
    relations = {left.claim_relation, right.claim_relation}

    if (
        policy.detect_relation_opposition
        and left_value == right_value
        and relations == {"supports", "opposes"}
    ):
        return "relation_opposition"

    if left_value == right_value:
        return None

    positive_pair = (
        left.claim_relation in _POSITIVE_RELATIONS
        and right.claim_relation in _POSITIVE_RELATIONS
    )
    if not positive_pair:
        return None

    if left.claim_key in policy.exclusive_claim_keys:
        return "exclusive_value_conflict"

    normalized_pair = (
        left.claim_key,
        *sorted((left_value, right_value)),
    )
    if normalized_pair in policy.exclusive_value_pairs:
        return "exclusive_value_conflict"

    return None


def _build_contradiction(
    *,
    kind: MultiLaboratoryEvidenceContradictionKind,
    left: MultiLaboratoryEvidenceItem,
    right: MultiLaboratoryEvidenceItem,
    canonical_by_ref: dict[str, str],
    groups_by_digest: dict[str, MultiLaboratoryEvidenceDigestGroup],
    policy_digest: str,
) -> MultiLaboratoryEvidenceContradiction:
    if left.evidence_ref > right.evidence_ref:
        left, right = right, left
    group_values = tuple(
        groups_by_digest[digest]
        for digest in sorted(
            {left.digest_sha256, right.digest_sha256}
        )
    )
    source_refs = tuple(
        sorted(
            {
                source_ref
                for group in group_values
                for source_ref in group.source_refs
            }
        )
    )
    laboratory_refs = tuple(
        sorted(
            {
                laboratory_ref
                for group in group_values
                for laboratory_ref in group.laboratory_refs
            }
        )
    )
    specialist_refs = tuple(
        sorted({left.specialist_ref, right.specialist_ref})
    )
    payload = {
        "schema": MULTI_LABORATORY_EVIDENCE_CONTRADICTION_SCHEMA,
        "contradiction_kind": kind,
        "claim_key": left.claim_key,
        "left_evidence_ref": left.evidence_ref,
        "right_evidence_ref": right.evidence_ref,
        "left_canonical_evidence_ref": canonical_by_ref[
            left.evidence_ref
        ],
        "right_canonical_evidence_ref": canonical_by_ref[
            right.evidence_ref
        ],
        "left_claim_value": left.claim_value,
        "right_claim_value": right.claim_value,
        "left_claim_relation": left.claim_relation,
        "right_claim_relation": right.claim_relation,
        "content_digests": sorted(
            {left.digest_sha256, right.digest_sha256}
        ),
        "source_refs": list(source_refs),
        "laboratory_refs": list(laboratory_refs),
        "specialist_refs": list(specialist_refs),
        "policy_digest": policy_digest,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return MultiLaboratoryEvidenceContradiction(
        schema=MULTI_LABORATORY_EVIDENCE_CONTRADICTION_SCHEMA,
        contradiction_ref="contradiction:" + sha256(encoded).hexdigest(),
        contradiction_kind=kind,
        claim_key=left.claim_key,
        left_evidence_ref=left.evidence_ref,
        right_evidence_ref=right.evidence_ref,
        left_canonical_evidence_ref=canonical_by_ref[left.evidence_ref],
        right_canonical_evidence_ref=canonical_by_ref[
            right.evidence_ref
        ],
        left_claim_value=left.claim_value,
        right_claim_value=right.claim_value,
        left_claim_relation=left.claim_relation,
        right_claim_relation=right.claim_relation,
        content_digests=tuple(
            sorted({left.digest_sha256, right.digest_sha256})
        ),
        source_refs=source_refs,
        laboratory_refs=laboratory_refs,
        specialist_refs=specialist_refs,
    )


def _result(
    *,
    deduplication: MultiLaboratoryEvidenceDeduplicationResult,
    policy: MultiLaboratoryEvidenceContradictionPolicy,
    contradictions: Sequence[MultiLaboratoryEvidenceContradiction],
    issues: Sequence[str],
    performed: bool,
) -> MultiLaboratoryEvidenceContradictionDetectionResult:
    contradiction_values = tuple(contradictions)
    contradiction_refs = tuple(
        item.contradiction_ref for item in contradiction_values
    )
    affected_evidence_refs = tuple(
        sorted(
            {
                evidence_ref
                for item in contradiction_values
                for evidence_ref in (
                    item.left_evidence_ref,
                    item.right_evidence_ref,
                )
            }
        )
    )
    affected_canonical_refs = {
        canonical_ref
        for item in contradiction_values
        for canonical_ref in (
            item.left_canonical_evidence_ref,
            item.right_canonical_evidence_ref,
        )
    }
    unaffected = tuple(
        ref
        for ref in deduplication.canonical_evidence_refs
        if ref not in affected_canonical_refs
    )
    issue_values = tuple(issues)
    valid = not issue_values and performed
    detection_digest = _detection_digest(
        deduplication=deduplication,
        policy=policy,
        contradictions=contradiction_values,
        issues=issue_values,
        performed=performed,
    )
    return MultiLaboratoryEvidenceContradictionDetectionResult(
        schema=(
            MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_SCHEMA
        ),
        valid=valid,
        issues=issue_values,
        aggregation_ref=deduplication.aggregation_ref,
        aggregation_digest=deduplication.aggregation_digest,
        deduplication_digest=deduplication.deduplication_digest,
        policy_ref=policy.policy_ref,
        policy_digest=policy.policy_digest,
        contradictions=contradiction_values,
        contradiction_refs=contradiction_refs,
        unresolved_contradictions=contradiction_values,
        unresolved_contradiction_refs=contradiction_refs,
        evidence_refs_with_contradictions=affected_evidence_refs,
        unaffected_canonical_evidence_refs=unaffected,
        contradiction_count=len(contradiction_values),
        unresolved_contradiction_count=len(contradiction_values),
        contradiction_free=not contradiction_values,
        contradiction_detection_performed=performed,
        ready_for_operator_weighting=valid,
        detection_digest=detection_digest,
    )


def _detection_digest(
    *,
    deduplication: MultiLaboratoryEvidenceDeduplicationResult,
    policy: MultiLaboratoryEvidenceContradictionPolicy,
    contradictions: Sequence[MultiLaboratoryEvidenceContradiction],
    issues: Sequence[str],
    performed: bool,
) -> str:
    payload = {
        "schema": (
            MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_SCHEMA
        ),
        "aggregation_ref": deduplication.aggregation_ref,
        "aggregation_digest": deduplication.aggregation_digest,
        "deduplication_digest": deduplication.deduplication_digest,
        "policy_digest": policy.policy_digest,
        "contradictions": [
            item.to_mapping() for item in contradictions
        ],
        "issues": list(issues),
        "contradiction_detection_performed": performed,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _normalize_claim_value(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MultiLaboratoryEvidenceContradictionDetectionError(
            "claim values must be non-empty"
        )
    return " ".join(value.split()).casefold()


def _require_claim_key(value: str) -> None:
    if not isinstance(value, str) or not _CLAIM_KEY_RE.fullmatch(value):
        raise MultiLaboratoryEvidenceContradictionDetectionError(
            "claim keys must use lowercase dotted identifier syntax"
        )


def _sorted_unique(
    name: str,
    values: Sequence[str],
    *,
    require_non_empty: bool = False,
    sha256_values: bool = False,
) -> tuple[str, ...]:
    normalized = tuple(sorted(values))
    if require_non_empty and not normalized:
        raise MultiLaboratoryEvidenceContradictionDetectionError(
            f"{name} cannot be empty"
        )
    if any(
        not isinstance(value, str) or not value.strip()
        for value in normalized
    ):
        raise MultiLaboratoryEvidenceContradictionDetectionError(
            f"{name} must contain non-empty strings"
        )
    if len(set(normalized)) != len(normalized):
        raise MultiLaboratoryEvidenceContradictionDetectionError(
            f"{name} must contain unique values"
        )
    if sha256_values and any(
        not _SHA256_RE.fullmatch(value) for value in normalized
    ):
        raise MultiLaboratoryEvidenceContradictionDetectionError(
            f"{name} must contain SHA-256 values"
        )
    return normalized


__all__ = (
    "MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_VERSION",
    "MULTI_LABORATORY_EVIDENCE_CONTRADICTION_POLICY_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_CONTRADICTION_SCHEMA",
    "MultiLaboratoryEvidenceContradiction",
    "MultiLaboratoryEvidenceContradictionDetectionError",
    "MultiLaboratoryEvidenceContradictionDetectionResult",
    "MultiLaboratoryEvidenceContradictionKind",
    "MultiLaboratoryEvidenceContradictionPolicy",
    "detect_multi_laboratory_evidence_contradictions",
)
