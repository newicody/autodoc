"""Immutable portable-specialist revision lineage contracts for phase 0285-r3.

The contracts reuse :class:`PortableSpecialistDescriptor` as the complete specialist
snapshot.  They preserve one stable ``specialist_ref`` across an append-only linear
lineage.  Approval, durable history, Scheduler selection and runtime execution remain
external responsibilities introduced by later phases.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
import re

from context.portable_specialist_contract_0284 import PortableSpecialistDescriptor
from context.specialist_capability_growth_proposal_contract_0285 import (
    SpecialistCapabilityGrowthProposal,
)

PORTABLE_SPECIALIST_REVISION_SCHEMA = "missipy.specialist.portable_revision.v1"
SPECIALIST_REVISION_LINEAGE_SCHEMA = "missipy.specialist.revision_lineage.v1"
PORTABLE_SPECIALIST_REVISION_LINEAGE_CONTRACT_VERSION = "0285.r3"

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_REVISION_PREFIXES = ("revision:",)
_LINEAGE_PREFIXES = ("lineage:",)
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


class PortableSpecialistRevisionLineageContractError(ValueError):
    """Raised when a portable-specialist revision lineage is incoherent."""


@dataclass(frozen=True, slots=True)
class PortableSpecialistRevision:
    """One immutable descriptor snapshot in a stable specialist lineage.

    The root revision bootstraps an existing descriptor and therefore has no source
    proposal.  Every later revision is linked to exactly one evidence-backed proposal.
    The revision does not embed an operator decision and cannot authorize itself.
    """

    schema: str
    revision_ref: str
    revision_number: int
    descriptor: PortableSpecialistDescriptor
    parent_revision_ref: str | None = None
    source_proposal_ref: str | None = None
    source_proposal_digest_sha256: str | None = None
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != PORTABLE_SPECIALIST_REVISION_SCHEMA:
            raise PortableSpecialistRevisionLineageContractError(
                "unsupported portable specialist revision schema"
            )
        _require_typed_ref(
            "revision_ref", self.revision_ref, required_prefixes=_REVISION_PREFIXES
        )
        if isinstance(self.revision_number, bool) or not isinstance(
            self.revision_number, int
        ):
            raise PortableSpecialistRevisionLineageContractError(
                "revision_number must be an integer"
            )
        if self.revision_number < 1:
            raise PortableSpecialistRevisionLineageContractError(
                "revision_number must be at least 1"
            )
        if not isinstance(self.descriptor, PortableSpecialistDescriptor):
            raise PortableSpecialistRevisionLineageContractError(
                "descriptor must be PortableSpecialistDescriptor"
            )

        if self.revision_number == 1:
            if self.parent_revision_ref is not None:
                raise PortableSpecialistRevisionLineageContractError(
                    "root revision must not declare parent_revision_ref"
                )
            if self.source_proposal_ref is not None:
                raise PortableSpecialistRevisionLineageContractError(
                    "root revision must not declare source_proposal_ref"
                )
            if self.source_proposal_digest_sha256 is not None:
                raise PortableSpecialistRevisionLineageContractError(
                    "root revision must not declare source proposal digest"
                )
            if self.evidence_refs:
                raise PortableSpecialistRevisionLineageContractError(
                    "root revision must not declare capability-growth evidence"
                )
        else:
            if self.parent_revision_ref is None:
                raise PortableSpecialistRevisionLineageContractError(
                    "non-root revision requires parent_revision_ref"
                )
            _require_typed_ref(
                "parent_revision_ref",
                self.parent_revision_ref,
                required_prefixes=_REVISION_PREFIXES,
            )
            if self.source_proposal_ref is None:
                raise PortableSpecialistRevisionLineageContractError(
                    "non-root revision requires source_proposal_ref"
                )
            _require_typed_ref(
                "source_proposal_ref",
                self.source_proposal_ref,
                required_prefixes=_PROPOSAL_PREFIXES,
            )
            _require_sha256(
                "source_proposal_digest_sha256",
                self.source_proposal_digest_sha256,
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

        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def specialist_ref(self) -> str:
        return self.descriptor.specialist_ref

    @property
    def specialist_version(self) -> str:
        return self.descriptor.specialist_version

    @property
    def descriptor_digest(self) -> str:
        payload = json.dumps(
            self.descriptor.to_mapping(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    @property
    def revision_digest(self) -> str:
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
            "revision_ref": self.revision_ref,
            "revision_number": self.revision_number,
            "specialist_ref": self.specialist_ref,
            "specialist_version": self.specialist_version,
            "parent_revision_ref": self.parent_revision_ref,
            "source_proposal_ref": self.source_proposal_ref,
            "source_proposal_digest_sha256": self.source_proposal_digest_sha256,
            "evidence_refs": list(self.evidence_refs),
            "descriptor": self.descriptor.to_mapping(),
            "descriptor_digest": self.descriptor_digest,
            "metadata": dict(self.metadata),
            "stable_specialist_identity": True,
            "approval_embedded": False,
            "operator_decision_required": self.revision_number > 1,
            "scheduler_selection_embedded": False,
            "durable_state_written": False,
            "runtime_attached": False,
        }
        if include_digest:
            mapping["revision_digest"] = self.revision_digest
        return mapping


@dataclass(frozen=True, slots=True)
class SpecialistRevisionLineage:
    """Append-only, single-parent lineage for one portable specialist identity."""

    schema: str
    lineage_ref: str
    specialist_ref: str
    revisions: tuple[PortableSpecialistRevision, ...]
    head_revision_ref: str
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_REVISION_LINEAGE_SCHEMA:
            raise PortableSpecialistRevisionLineageContractError(
                "unsupported specialist revision lineage schema"
            )
        _require_typed_ref(
            "lineage_ref", self.lineage_ref, required_prefixes=_LINEAGE_PREFIXES
        )
        _require_typed_ref(
            "specialist_ref",
            self.specialist_ref,
            required_prefixes=_SPECIALIST_PREFIXES,
        )
        revisions = tuple(self.revisions)
        if not revisions or not all(
            isinstance(item, PortableSpecialistRevision) for item in revisions
        ):
            raise PortableSpecialistRevisionLineageContractError(
                "revisions must contain PortableSpecialistRevision values"
            )
        ordered = tuple(sorted(revisions, key=lambda item: item.revision_number))
        expected_numbers = tuple(range(1, len(ordered) + 1))
        actual_numbers = tuple(item.revision_number for item in ordered)
        if actual_numbers != expected_numbers:
            raise PortableSpecialistRevisionLineageContractError(
                "revision numbers must be contiguous and start at 1"
            )

        revision_refs = tuple(item.revision_ref for item in ordered)
        if len(set(revision_refs)) != len(revision_refs):
            raise PortableSpecialistRevisionLineageContractError(
                "revision_ref values must be unique"
            )
        versions = tuple(item.specialist_version for item in ordered)
        if len(set(versions)) != len(versions):
            raise PortableSpecialistRevisionLineageContractError(
                "specialist versions must be unique within a lineage"
            )
        descriptor_digests = tuple(item.descriptor_digest for item in ordered)
        if len(set(descriptor_digests)) != len(descriptor_digests):
            raise PortableSpecialistRevisionLineageContractError(
                "descriptor snapshots must change between revisions"
            )
        proposal_refs = tuple(
            item.source_proposal_ref
            for item in ordered
            if item.source_proposal_ref is not None
        )
        if len(set(proposal_refs)) != len(proposal_refs):
            raise PortableSpecialistRevisionLineageContractError(
                "source proposals must be unique within a lineage"
            )

        for index, revision in enumerate(ordered):
            if revision.specialist_ref != self.specialist_ref:
                raise PortableSpecialistRevisionLineageContractError(
                    "all revisions must preserve lineage specialist_ref"
                )
            if index == 0:
                if revision.parent_revision_ref is not None:
                    raise PortableSpecialistRevisionLineageContractError(
                        "first revision must be the root"
                    )
                continue
            parent = ordered[index - 1]
            if revision.parent_revision_ref != parent.revision_ref:
                raise PortableSpecialistRevisionLineageContractError(
                    "each revision must reference the immediately preceding revision"
                )

        if self.head_revision_ref != ordered[-1].revision_ref:
            raise PortableSpecialistRevisionLineageContractError(
                "head_revision_ref must identify the latest revision"
            )
        object.__setattr__(self, "revisions", ordered)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def head_revision(self) -> PortableSpecialistRevision:
        return self.revisions[-1]

    @property
    def lineage_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def append(self, revision: PortableSpecialistRevision) -> SpecialistRevisionLineage:
        """Return a new lineage with one validated child revision appended."""
        if not isinstance(revision, PortableSpecialistRevision):
            raise TypeError("revision must be PortableSpecialistRevision")
        expected_number = len(self.revisions) + 1
        if revision.revision_number != expected_number:
            raise PortableSpecialistRevisionLineageContractError(
                "appended revision_number must follow the current head"
            )
        if revision.parent_revision_ref != self.head_revision_ref:
            raise PortableSpecialistRevisionLineageContractError(
                "appended revision must reference the current head"
            )
        if revision.specialist_ref != self.specialist_ref:
            raise PortableSpecialistRevisionLineageContractError(
                "appended revision must preserve specialist_ref"
            )
        return replace(
            self,
            revisions=(*self.revisions, revision),
            head_revision_ref=revision.revision_ref,
        )

    def to_mapping(self, *, include_digest: bool = True) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "lineage_ref": self.lineage_ref,
            "specialist_ref": self.specialist_ref,
            "head_revision_ref": self.head_revision_ref,
            "revisions": [item.to_mapping() for item in self.revisions],
            "metadata": dict(self.metadata),
            "append_only": True,
            "linear_single_parent": True,
            "operator_decision_external": True,
            "scheduler_remains_only_orchestrator": True,
            "sql_history_not_written": True,
            "qdrant_projection_not_written": True,
            "eventbus_observation_not_published": True,
            "github_mutation_performed": False,
        }
        if include_digest:
            mapping["lineage_digest"] = self.lineage_digest
        return mapping


def validate_revision_against_growth_proposal(
    revision: PortableSpecialistRevision,
    proposal: SpecialistCapabilityGrowthProposal,
    parent_revision: PortableSpecialistRevision,
) -> tuple[str, ...]:
    """Validate one proposed child revision against the r2 proposal and its parent.

    The function is inspection-only.  It does not approve the revision or append it to
    durable history.
    """
    if not isinstance(revision, PortableSpecialistRevision):
        raise TypeError("revision must be PortableSpecialistRevision")
    if not isinstance(proposal, SpecialistCapabilityGrowthProposal):
        raise TypeError("proposal must be SpecialistCapabilityGrowthProposal")
    if not isinstance(parent_revision, PortableSpecialistRevision):
        raise TypeError("parent_revision must be PortableSpecialistRevision")

    issues: list[str] = []
    if revision.revision_number == 1:
        issues.append("root revision cannot be produced from a growth proposal")
    if revision.parent_revision_ref != parent_revision.revision_ref:
        issues.append("revision parent must match the supplied parent revision")
    if revision.specialist_ref != parent_revision.specialist_ref:
        issues.append("revision must preserve parent specialist_ref")
    if proposal.specialist_ref != revision.specialist_ref:
        issues.append("proposal specialist_ref must match revision specialist_ref")
    if proposal.base_specialist_version != parent_revision.specialist_version:
        issues.append("proposal base version must match parent specialist version")
    if revision.source_proposal_ref != proposal.proposal_ref:
        issues.append("revision source proposal ref must match proposal_ref")
    if revision.source_proposal_digest_sha256 != proposal.proposal_digest:
        issues.append("revision source proposal digest must match proposal_digest")

    revision_evidence = frozenset(revision.evidence_refs)
    proposal_evidence = frozenset(item.evidence_ref for item in proposal.evidence_refs)
    if revision_evidence != proposal_evidence:
        issues.append("revision evidence refs must match proposal evidence refs")

    capabilities = frozenset(
        item.capability for item in revision.descriptor.capabilities
    )
    if proposal.action in {"add", "refine", "restore"} and (
        proposal.capability not in capabilities
    ):
        issues.append("resulting descriptor must contain the proposed capability")

    accepted = frozenset(revision.descriptor.accepted_input_contract_refs)
    produced = frozenset(revision.descriptor.produced_output_contract_refs)
    if not set(proposal.requested_input_contract_refs).issubset(accepted):
        issues.append("resulting descriptor must accept proposal input contracts")
    if not set(proposal.requested_output_contract_refs).issubset(produced):
        issues.append("resulting descriptor must produce proposal output contracts")

    laboratory_capabilities = frozenset(
        capability
        for binding in revision.descriptor.laboratory_bindings
        for capability in binding.required_laboratory_capabilities
    )
    requested_laboratory_capabilities = frozenset(
        ref.removeprefix("laboratory-capability:")
        for ref in proposal.requested_laboratory_capability_refs
    )
    if not requested_laboratory_capabilities.issubset(laboratory_capabilities):
        issues.append(
            "resulting descriptor bindings must satisfy proposal laboratory capabilities"
        )
    return tuple(dict.fromkeys(issues))


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefixes: tuple[str, ...] | None = None,
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise PortableSpecialistRevisionLineageContractError(
            f"{name} must be a typed reference"
        )
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise PortableSpecialistRevisionLineageContractError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_sha256(name: str, value: str | None) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise PortableSpecialistRevisionLineageContractError(
            f"{name} must be a lowercase SHA-256 digest"
        )


def _normalize_refs(
    name: str,
    refs: Sequence[str],
    *,
    required_prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    values = tuple(refs)
    if not values:
        raise PortableSpecialistRevisionLineageContractError(
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
        if not isinstance(key, str) or not key.strip():
            raise PortableSpecialistRevisionLineageContractError(
                "metadata key must be non-empty"
            )
        if not isinstance(value, str) or not value.strip():
            raise PortableSpecialistRevisionLineageContractError(
                "metadata value must be non-empty"
            )
        normalized[key.strip()] = value.strip()
    return tuple(sorted(normalized.items()))


__all__ = (
    "PORTABLE_SPECIALIST_REVISION_LINEAGE_CONTRACT_VERSION",
    "PORTABLE_SPECIALIST_REVISION_SCHEMA",
    "SPECIALIST_REVISION_LINEAGE_SCHEMA",
    "PortableSpecialistRevision",
    "PortableSpecialistRevisionLineageContractError",
    "SpecialistRevisionLineage",
    "validate_revision_against_growth_proposal",
)
