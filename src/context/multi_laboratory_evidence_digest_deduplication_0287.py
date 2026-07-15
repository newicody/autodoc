"""Digest-based evidence deduplication for phase 0287-r4.

The contract consumes one r2 aggregate and its r3 provenance chains. It groups
content-equivalent evidence by the existing SHA-256 digest, chooses a
deterministic canonical evidence reference, preserves every provenance/source
alias and keeps claim variants visible for r5 contradiction detection.

No evidence is deleted from the returned proof. The original items remain
available beside the canonical view.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re

from context.multi_laboratory_evidence_aggregation_contract_0287 import (
    MultiLaboratoryEvidenceAggregate,
    MultiLaboratoryEvidenceItem,
)
from context.multi_laboratory_evidence_provenance_contract_0287 import (
    MultiLaboratoryEvidenceProvenance,
    validate_multi_laboratory_evidence_provenance,
)


MULTI_LABORATORY_EVIDENCE_DIGEST_GROUP_SCHEMA = (
    "missipy.multi_laboratory.evidence_digest_group.v1"
)
MULTI_LABORATORY_EVIDENCE_DEDUPLICATION_SCHEMA = (
    "missipy.multi_laboratory.evidence_deduplication.v1"
)
MULTI_LABORATORY_EVIDENCE_DIGEST_DEDUPLICATION_VERSION = "0287.r4"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class MultiLaboratoryEvidenceDigestDeduplicationError(ValueError):
    """Raised when a digest group or deduplication proof is incoherent."""


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceDigestGroup:
    """One content digest and every evidence/provenance alias attached to it."""

    schema: str
    digest_sha256: str
    canonical_evidence_ref: str
    member_evidence_refs: tuple[str, ...]
    duplicate_evidence_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    source_identity_digests: tuple[str, ...]
    laboratory_refs: tuple[str, ...]
    specialist_refs: tuple[str, ...]
    claim_signatures: tuple[str, ...]
    claim_variant_evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_DIGEST_GROUP_SCHEMA:
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "unsupported digest group schema"
            )
        if not _SHA256_RE.fullmatch(self.digest_sha256):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "digest_sha256 must be a lowercase SHA-256"
            )
        members = _sorted_unique(
            "member_evidence_refs",
            self.member_evidence_refs,
            require_non_empty=True,
        )
        if self.canonical_evidence_ref != members[0]:
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "canonical_evidence_ref must be the first sorted member"
            )
        duplicates = _sorted_unique(
            "duplicate_evidence_refs",
            self.duplicate_evidence_refs,
        )
        if duplicates != tuple(
            ref for ref in members if ref != self.canonical_evidence_ref
        ):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "duplicate_evidence_refs must contain every non-canonical member"
            )
        provenances = _sorted_unique(
            "provenance_refs",
            self.provenance_refs,
            require_non_empty=True,
        )
        if len(provenances) != len(members):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "each digest member must preserve one provenance_ref"
            )
        sources = _sorted_unique(
            "source_refs",
            self.source_refs,
            require_non_empty=True,
        )
        source_digests = tuple(self.source_identity_digests)
        expected_source_digests = tuple(
            _source_identity_digest(source_ref) for source_ref in sources
        )
        if source_digests != expected_source_digests:
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "source_identity_digests do not match source_refs"
            )
        laboratories = _sorted_unique(
            "laboratory_refs",
            self.laboratory_refs,
            require_non_empty=True,
        )
        specialists = _sorted_unique(
            "specialist_refs",
            self.specialist_refs,
            require_non_empty=True,
        )
        signatures = _sorted_unique(
            "claim_signatures",
            self.claim_signatures,
            require_non_empty=True,
        )
        variants = _sorted_unique(
            "claim_variant_evidence_refs",
            self.claim_variant_evidence_refs,
        )
        if not set(variants).issubset(members):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "claim_variant_evidence_refs must belong to the digest group"
            )
        if len(signatures) > 1 and variants != members:
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "all members must remain visible when claim variants exist"
            )
        if len(signatures) == 1 and variants:
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "claim variants cannot exist for one claim signature"
            )

        object.__setattr__(self, "member_evidence_refs", members)
        object.__setattr__(self, "duplicate_evidence_refs", duplicates)
        object.__setattr__(self, "provenance_refs", provenances)
        object.__setattr__(self, "source_refs", sources)
        object.__setattr__(
            self,
            "source_identity_digests",
            source_digests,
        )
        object.__setattr__(self, "laboratory_refs", laboratories)
        object.__setattr__(self, "specialist_refs", specialists)
        object.__setattr__(self, "claim_signatures", signatures)
        object.__setattr__(
            self,
            "claim_variant_evidence_refs",
            variants,
        )

    @property
    def cross_source_corroborated(self) -> bool:
        return len(self.source_refs) > 1

    @property
    def cross_laboratory_corroborated(self) -> bool:
        return len(self.laboratory_refs) > 1

    @property
    def group_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_group_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(
        self,
        *,
        include_group_digest: bool = True,
    ) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "digest_sha256": self.digest_sha256,
            "canonical_evidence_ref": self.canonical_evidence_ref,
            "member_evidence_refs": list(self.member_evidence_refs),
            "duplicate_evidence_refs": list(
                self.duplicate_evidence_refs
            ),
            "provenance_refs": list(self.provenance_refs),
            "source_refs": list(self.source_refs),
            "source_identity_digests": list(
                self.source_identity_digests
            ),
            "laboratory_refs": list(self.laboratory_refs),
            "specialist_refs": list(self.specialist_refs),
            "claim_signatures": list(self.claim_signatures),
            "claim_variant_evidence_refs": list(
                self.claim_variant_evidence_refs
            ),
            "cross_source_corroborated": (
                self.cross_source_corroborated
            ),
            "cross_laboratory_corroborated": (
                self.cross_laboratory_corroborated
            ),
        }
        if include_group_digest:
            mapping["group_digest"] = self.group_digest
        return mapping


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceDeduplicationResult:
    """Immutable canonical view that preserves every original evidence item."""

    schema: str
    valid: bool
    issues: tuple[str, ...]
    aggregation_ref: str
    aggregation_digest: str
    provenance_validation_digest: str
    retained_evidence_items: tuple[MultiLaboratoryEvidenceItem, ...]
    canonical_evidence_items: tuple[MultiLaboratoryEvidenceItem, ...]
    digest_groups: tuple[MultiLaboratoryEvidenceDigestGroup, ...]
    canonical_evidence_refs: tuple[str, ...]
    duplicate_evidence_refs: tuple[str, ...]
    evidence_aliases: tuple[tuple[str, str], ...]
    source_identity_digests: tuple[str, ...]
    claim_variant_evidence_refs: tuple[str, ...]
    original_evidence_count: int
    canonical_evidence_count: int
    duplicate_evidence_count: int
    content_duplicates_found: bool
    cross_source_corroboration_group_count: int
    deduplication_performed: bool
    deduplication_digest: str
    authoritative: bool = field(default=False, init=False)
    approved: bool = field(default=False, init=False)
    provenance_chain_validated: bool = field(default=True, init=False)
    contradiction_detection_performed: bool = field(
        default=False,
        init=False,
    )
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
        if self.schema != MULTI_LABORATORY_EVIDENCE_DEDUPLICATION_SCHEMA:
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "unsupported deduplication result schema"
            )
        if not _SHA256_RE.fullmatch(self.aggregation_digest):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "aggregation_digest must be SHA-256"
            )
        if not _SHA256_RE.fullmatch(
            self.provenance_validation_digest
        ):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "provenance_validation_digest must be SHA-256"
            )
        if not _SHA256_RE.fullmatch(self.deduplication_digest):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "deduplication_digest must be SHA-256"
            )
        issues = tuple(self.issues)
        retained = tuple(self.retained_evidence_items)
        canonical = tuple(self.canonical_evidence_items)
        groups = tuple(self.digest_groups)
        canonical_refs = tuple(self.canonical_evidence_refs)
        duplicate_refs = tuple(self.duplicate_evidence_refs)
        aliases = tuple(self.evidence_aliases)
        source_digests = tuple(self.source_identity_digests)
        variant_refs = tuple(self.claim_variant_evidence_refs)

        if self.valid != (not issues and self.deduplication_performed):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "valid flag does not match issues/deduplication state"
            )
        if self.original_evidence_count != len(retained):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "original_evidence_count does not match retained items"
            )
        if self.canonical_evidence_count != len(canonical):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "canonical_evidence_count does not match canonical items"
            )
        if self.duplicate_evidence_count != len(duplicate_refs):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "duplicate_evidence_count does not match duplicate refs"
            )
        if self.content_duplicates_found != bool(duplicate_refs):
            raise MultiLaboratoryEvidenceDigestDeduplicationError(
                "content_duplicates_found does not match duplicate refs"
            )
        if self.valid:
            retained_refs = tuple(
                item.evidence_ref for item in retained
            )
            if len(set(retained_refs)) != len(retained_refs):
                raise MultiLaboratoryEvidenceDigestDeduplicationError(
                    "retained evidence refs must remain unique"
                )
            if canonical_refs != tuple(
                item.evidence_ref for item in canonical
            ):
                raise MultiLaboratoryEvidenceDigestDeduplicationError(
                    "canonical refs do not match canonical items"
                )
            if len(groups) != len(canonical):
                raise MultiLaboratoryEvidenceDigestDeduplicationError(
                    "each canonical item must have one digest group"
                )
            expected_aliases = tuple(
                sorted(
                    (
                        duplicate_ref,
                        group.canonical_evidence_ref,
                    )
                    for group in groups
                    for duplicate_ref in group.duplicate_evidence_refs
                )
            )
            if aliases != expected_aliases:
                raise MultiLaboratoryEvidenceDigestDeduplicationError(
                    "evidence_aliases do not match digest groups"
                )
            if set(canonical_refs) & set(duplicate_refs):
                raise MultiLaboratoryEvidenceDigestDeduplicationError(
                    "canonical and duplicate refs must be disjoint"
                )
            if set(canonical_refs) | set(duplicate_refs) != set(
                retained_refs
            ):
                raise MultiLaboratoryEvidenceDigestDeduplicationError(
                    "canonical and duplicate refs must cover all evidence"
                )

        object.__setattr__(self, "issues", issues)
        object.__setattr__(
            self,
            "retained_evidence_items",
            retained,
        )
        object.__setattr__(
            self,
            "canonical_evidence_items",
            canonical,
        )
        object.__setattr__(self, "digest_groups", groups)
        object.__setattr__(
            self,
            "canonical_evidence_refs",
            canonical_refs,
        )
        object.__setattr__(
            self,
            "duplicate_evidence_refs",
            duplicate_refs,
        )
        object.__setattr__(self, "evidence_aliases", aliases)
        object.__setattr__(
            self,
            "source_identity_digests",
            source_digests,
        )
        object.__setattr__(
            self,
            "claim_variant_evidence_refs",
            variant_refs,
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "aggregation_ref": self.aggregation_ref,
            "aggregation_digest": self.aggregation_digest,
            "provenance_validation_digest": (
                self.provenance_validation_digest
            ),
            "retained_evidence_items": [
                item.to_mapping()
                for item in self.retained_evidence_items
            ],
            "canonical_evidence_items": [
                item.to_mapping()
                for item in self.canonical_evidence_items
            ],
            "digest_groups": [
                group.to_mapping() for group in self.digest_groups
            ],
            "canonical_evidence_refs": list(
                self.canonical_evidence_refs
            ),
            "duplicate_evidence_refs": list(
                self.duplicate_evidence_refs
            ),
            "evidence_aliases": [
                {
                    "duplicate_evidence_ref": duplicate_ref,
                    "canonical_evidence_ref": canonical_ref,
                }
                for duplicate_ref, canonical_ref in self.evidence_aliases
            ],
            "source_identity_digests": list(
                self.source_identity_digests
            ),
            "claim_variant_evidence_refs": list(
                self.claim_variant_evidence_refs
            ),
            "original_evidence_count": self.original_evidence_count,
            "canonical_evidence_count": self.canonical_evidence_count,
            "duplicate_evidence_count": self.duplicate_evidence_count,
            "content_duplicates_found": self.content_duplicates_found,
            "cross_source_corroboration_group_count": (
                self.cross_source_corroboration_group_count
            ),
            "deduplication_performed": self.deduplication_performed,
            "deduplication_digest": self.deduplication_digest,
            "authoritative": False,
            "approved": False,
            "provenance_chain_validated": self.valid,
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


def deduplicate_multi_laboratory_evidence(
    aggregate: MultiLaboratoryEvidenceAggregate,
    provenances: Sequence[MultiLaboratoryEvidenceProvenance],
) -> MultiLaboratoryEvidenceDeduplicationResult:
    """Build a deterministic canonical digest view after r3 validation."""

    if not isinstance(aggregate, MultiLaboratoryEvidenceAggregate):
        raise TypeError("aggregate must be MultiLaboratoryEvidenceAggregate")
    provenance_values = tuple(provenances)
    if not all(
        isinstance(value, MultiLaboratoryEvidenceProvenance)
        for value in provenance_values
    ):
        raise TypeError(
            "provenances must contain MultiLaboratoryEvidenceProvenance"
        )

    validation = validate_multi_laboratory_evidence_provenance(
        aggregate,
        provenance_values,
    )
    if not validation.valid:
        issues = tuple(
            f"provenance validation: {issue}"
            for issue in validation.issues
        )
        return MultiLaboratoryEvidenceDeduplicationResult(
            schema=MULTI_LABORATORY_EVIDENCE_DEDUPLICATION_SCHEMA,
            valid=False,
            issues=issues
            or ("provenance validation did not authorize deduplication",),
            aggregation_ref=aggregate.aggregation_ref,
            aggregation_digest=aggregate.aggregation_digest,
            provenance_validation_digest=validation.validation_digest,
            retained_evidence_items=tuple(aggregate.evidence_items),
            canonical_evidence_items=(),
            digest_groups=(),
            canonical_evidence_refs=(),
            duplicate_evidence_refs=(),
            evidence_aliases=(),
            source_identity_digests=(),
            claim_variant_evidence_refs=(),
            original_evidence_count=len(aggregate.evidence_items),
            canonical_evidence_count=0,
            duplicate_evidence_count=0,
            content_duplicates_found=False,
            cross_source_corroboration_group_count=0,
            deduplication_performed=False,
            deduplication_digest=_deduplication_digest(
                aggregate=aggregate,
                validation_digest=validation.validation_digest,
                groups=(),
                issues=issues,
            ),
        )

    by_provenance_ref = {
        value.provenance_ref: value for value in provenance_values
    }
    grouped: dict[str, list[MultiLaboratoryEvidenceItem]] = {}
    for item in aggregate.evidence_items:
        grouped.setdefault(item.digest_sha256, []).append(item)

    groups: list[MultiLaboratoryEvidenceDigestGroup] = []
    canonical_items: list[MultiLaboratoryEvidenceItem] = []
    duplicate_refs: list[str] = []
    aliases: list[tuple[str, str]] = []
    variant_refs: set[str] = set()
    source_identity_digests: set[str] = set()

    for content_digest in sorted(grouped):
        members = tuple(
            sorted(
                grouped[content_digest],
                key=lambda item: item.evidence_ref,
            )
        )
        canonical = members[0]
        member_refs = tuple(item.evidence_ref for item in members)
        duplicate_group_refs = member_refs[1:]
        sources = tuple(sorted({item.source_ref for item in members}))
        source_digests = tuple(
            _source_identity_digest(source_ref)
            for source_ref in sources
        )
        claim_signatures = tuple(
            sorted({_claim_signature(item) for item in members})
        )
        variants = member_refs if len(claim_signatures) > 1 else ()
        group_provenances = tuple(
            by_provenance_ref[item.provenance_ref]
            for item in members
        )
        group = MultiLaboratoryEvidenceDigestGroup(
            schema=MULTI_LABORATORY_EVIDENCE_DIGEST_GROUP_SCHEMA,
            digest_sha256=content_digest,
            canonical_evidence_ref=canonical.evidence_ref,
            member_evidence_refs=member_refs,
            duplicate_evidence_refs=duplicate_group_refs,
            provenance_refs=tuple(
                value.provenance_ref for value in group_provenances
            ),
            source_refs=sources,
            source_identity_digests=source_digests,
            laboratory_refs=tuple(
                value.laboratory_ref for value in group_provenances
            ),
            specialist_refs=tuple(
                item.specialist_ref for item in members
            ),
            claim_signatures=claim_signatures,
            claim_variant_evidence_refs=variants,
        )
        groups.append(group)
        canonical_items.append(canonical)
        duplicate_refs.extend(duplicate_group_refs)
        aliases.extend(
            (duplicate_ref, canonical.evidence_ref)
            for duplicate_ref in duplicate_group_refs
        )
        variant_refs.update(variants)
        source_identity_digests.update(source_digests)

    group_values = tuple(
        sorted(groups, key=lambda group: group.digest_sha256)
    )
    issues: tuple[str, ...] = ()
    return MultiLaboratoryEvidenceDeduplicationResult(
        schema=MULTI_LABORATORY_EVIDENCE_DEDUPLICATION_SCHEMA,
        valid=True,
        issues=issues,
        aggregation_ref=aggregate.aggregation_ref,
        aggregation_digest=aggregate.aggregation_digest,
        provenance_validation_digest=validation.validation_digest,
        retained_evidence_items=tuple(aggregate.evidence_items),
        canonical_evidence_items=tuple(
            sorted(
                canonical_items,
                key=lambda item: item.evidence_ref,
            )
        ),
        digest_groups=group_values,
        canonical_evidence_refs=tuple(
            sorted(item.evidence_ref for item in canonical_items)
        ),
        duplicate_evidence_refs=tuple(sorted(duplicate_refs)),
        evidence_aliases=tuple(sorted(aliases)),
        source_identity_digests=tuple(
            sorted(source_identity_digests)
        ),
        claim_variant_evidence_refs=tuple(sorted(variant_refs)),
        original_evidence_count=len(aggregate.evidence_items),
        canonical_evidence_count=len(canonical_items),
        duplicate_evidence_count=len(duplicate_refs),
        content_duplicates_found=bool(duplicate_refs),
        cross_source_corroboration_group_count=sum(
            group.cross_source_corroborated for group in group_values
        ),
        deduplication_performed=True,
        deduplication_digest=_deduplication_digest(
            aggregate=aggregate,
            validation_digest=validation.validation_digest,
            groups=group_values,
            issues=issues,
        ),
    )


def _claim_signature(item: MultiLaboratoryEvidenceItem) -> str:
    payload = {
        "claim_key": item.claim_key,
        "claim_value": item.claim_value,
        "claim_relation": item.claim_relation,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _source_identity_digest(source_ref: str) -> str:
    return sha256(source_ref.encode("utf-8")).hexdigest()


def _deduplication_digest(
    *,
    aggregate: MultiLaboratoryEvidenceAggregate,
    validation_digest: str,
    groups: Sequence[MultiLaboratoryEvidenceDigestGroup],
    issues: Sequence[str],
) -> str:
    payload = {
        "schema": MULTI_LABORATORY_EVIDENCE_DEDUPLICATION_SCHEMA,
        "aggregation_ref": aggregate.aggregation_ref,
        "aggregation_digest": aggregate.aggregation_digest,
        "provenance_validation_digest": validation_digest,
        "digest_groups": [
            group.to_mapping() for group in groups
        ],
        "issues": list(issues),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _sorted_unique(
    name: str,
    values: Sequence[str],
    *,
    require_non_empty: bool = False,
) -> tuple[str, ...]:
    normalized = tuple(sorted(values))
    if require_non_empty and not normalized:
        raise MultiLaboratoryEvidenceDigestDeduplicationError(
            f"{name} cannot be empty"
        )
    if any(not isinstance(value, str) or not value.strip() for value in normalized):
        raise MultiLaboratoryEvidenceDigestDeduplicationError(
            f"{name} must contain non-empty strings"
        )
    if len(set(normalized)) != len(normalized):
        raise MultiLaboratoryEvidenceDigestDeduplicationError(
            f"{name} must contain unique values"
        )
    return normalized


__all__ = (
    "MULTI_LABORATORY_EVIDENCE_DEDUPLICATION_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_DIGEST_DEDUPLICATION_VERSION",
    "MULTI_LABORATORY_EVIDENCE_DIGEST_GROUP_SCHEMA",
    "MultiLaboratoryEvidenceDeduplicationResult",
    "MultiLaboratoryEvidenceDigestDeduplicationError",
    "MultiLaboratoryEvidenceDigestGroup",
    "deduplicate_multi_laboratory_evidence",
)
