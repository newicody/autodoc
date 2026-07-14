"""Append-only durable-history port for specialist capability growth, phase 0285-r5.

The module records only operator-approved r4 decisions and their complete r3
portable-specialist revision snapshots.  SQL is the authoritative destination by
contract.  The included in-memory adapter is deterministic and test-only: it performs
no SQL, Qdrant, Scheduler, laboratory, EventBus or GitHub side effect.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Protocol, runtime_checkable

from context.portable_specialist_revision_lineage_contract_0285 import (
    PortableSpecialistRevision,
    SpecialistRevisionLineage,
)
from context.specialist_capability_growth_operator_gate_0285 import (
    SpecialistCapabilityGrowthDecision,
)

SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_COMMAND_SCHEMA = (
    "missipy.specialist.capability_growth_history_append_command.v1"
)
SPECIALIST_CAPABILITY_GROWTH_HISTORY_ENTRY_SCHEMA = (
    "missipy.specialist.capability_growth_history_entry.v1"
)
SPECIALIST_CAPABILITY_GROWTH_HISTORY_SNAPSHOT_SCHEMA = (
    "missipy.specialist.capability_growth_history_snapshot.v1"
)
SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_RESULT_SCHEMA = (
    "missipy.specialist.capability_growth_history_append_result.v1"
)
SPECIALIST_CAPABILITY_GROWTH_DURABLE_HISTORY_CONTRACT_VERSION = "0285.r5"

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HISTORY_PREFIXES = ("history:",)
_HISTORY_ENTRY_PREFIXES = ("history-entry:",)
_SQL_PREFIXES = ("sql:",)


class SpecialistCapabilityGrowthDurableHistoryError(ValueError):
    """Raised when a durable-history command, entry or chain is incoherent."""


class SpecialistCapabilityGrowthHistoryConflictError(
    SpecialistCapabilityGrowthDurableHistoryError
):
    """Raised when append-only or optimistic-concurrency constraints are violated."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthHistoryEntry:
    """One immutable, SQL-addressed, operator-approved history entry."""

    schema: str
    history_ref: str
    entry_ref: str
    sql_ref: str
    sequence_number: int
    base_lineage_digest_sha256: str
    decision: SpecialistCapabilityGrowthDecision
    revision: PortableSpecialistRevision
    resulting_lineage: SpecialistRevisionLineage
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_HISTORY_ENTRY_SCHEMA:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "unsupported specialist capability growth history entry schema"
            )
        _require_typed_ref(
            "history_ref", self.history_ref, required_prefixes=_HISTORY_PREFIXES
        )
        _require_typed_ref(
            "entry_ref", self.entry_ref, required_prefixes=_HISTORY_ENTRY_PREFIXES
        )
        _require_typed_ref("sql_ref", self.sql_ref, required_prefixes=_SQL_PREFIXES)
        _require_positive_integer("sequence_number", self.sequence_number)
        _require_sha256(
            "base_lineage_digest_sha256", self.base_lineage_digest_sha256
        )
        if not isinstance(self.decision, SpecialistCapabilityGrowthDecision):
            raise TypeError("decision must be SpecialistCapabilityGrowthDecision")
        if not isinstance(self.revision, PortableSpecialistRevision):
            raise TypeError("revision must be PortableSpecialistRevision")
        if not isinstance(self.resulting_lineage, SpecialistRevisionLineage):
            raise TypeError("resulting_lineage must be SpecialistRevisionLineage")
        if not self.decision.revision_authorized:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "history entry requires an operator-approved revision"
            )
        if self.decision.base_lineage_digest_sha256 != self.base_lineage_digest_sha256:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "decision base lineage digest must match history entry"
            )
        if self.decision.base_lineage_ref != self.resulting_lineage.lineage_ref:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "decision base lineage ref must match resulting lineage"
            )
        if self.decision.candidate_revision_ref != self.revision.revision_ref:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "decision candidate revision ref must match history revision"
            )
        if (
            self.decision.candidate_revision_digest_sha256
            != self.revision.revision_digest
        ):
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "decision candidate revision digest must match history revision"
            )
        if self.decision.specialist_ref != self.revision.specialist_ref:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "decision specialist_ref must match history revision"
            )
        if self.resulting_lineage.specialist_ref != self.revision.specialist_ref:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "resulting lineage must preserve revision specialist_ref"
            )
        if self.resulting_lineage.head_revision_ref != self.revision.revision_ref:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "resulting lineage head must be the recorded revision"
            )
        if self.resulting_lineage.head_revision.revision_digest != self.revision.revision_digest:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "resulting lineage head digest must match the recorded revision"
            )
        if self.decision.proposal_ref != self.revision.source_proposal_ref:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "decision proposal ref must match revision source proposal"
            )
        if (
            self.decision.proposal_digest_sha256
            != self.revision.source_proposal_digest_sha256
        ):
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "decision proposal digest must match revision source proposal"
            )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def specialist_ref(self) -> str:
        return self.revision.specialist_ref

    @property
    def entry_digest(self) -> str:
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
            "history_ref": self.history_ref,
            "entry_ref": self.entry_ref,
            "sql_ref": self.sql_ref,
            "sequence_number": self.sequence_number,
            "specialist_ref": self.specialist_ref,
            "base_lineage_digest_sha256": self.base_lineage_digest_sha256,
            "decision": self.decision.to_mapping(),
            "revision": self.revision.to_mapping(),
            "resulting_lineage": self.resulting_lineage.to_mapping(),
            "metadata": dict(self.metadata),
            "append_only": True,
            "sql_authoritative": True,
            "qdrant_authoritative": False,
            "scheduler_selection_performed": False,
            "scheduler_dispatch_performed": False,
            "laboratory_execution_performed": False,
            "eventbus_observation_published": False,
            "github_mutation_performed": False,
        }
        if include_digest:
            mapping["entry_digest"] = self.entry_digest
        return mapping


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthHistorySnapshot:
    """Validated append-only history for one specialist identity."""

    schema: str
    history_ref: str
    specialist_ref: str
    entries: tuple[SpecialistCapabilityGrowthHistoryEntry, ...]
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_HISTORY_SNAPSHOT_SCHEMA:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "unsupported specialist capability growth history snapshot schema"
            )
        _require_typed_ref(
            "history_ref", self.history_ref, required_prefixes=_HISTORY_PREFIXES
        )
        _require_typed_ref("specialist_ref", self.specialist_ref)
        entries = tuple(self.entries)
        if not entries or not all(
            isinstance(item, SpecialistCapabilityGrowthHistoryEntry)
            for item in entries
        ):
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "entries must contain history entry values"
            )
        ordered = tuple(sorted(entries, key=lambda item: item.sequence_number))
        if tuple(item.sequence_number for item in ordered) != tuple(
            range(1, len(ordered) + 1)
        ):
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "history sequence numbers must be contiguous and start at 1"
            )
        if any(item.history_ref != self.history_ref for item in ordered):
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "all entries must preserve history_ref"
            )
        if any(item.specialist_ref != self.specialist_ref for item in ordered):
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "all entries must preserve specialist_ref"
            )
        _require_unique("entry_ref", tuple(item.entry_ref for item in ordered))
        _require_unique("sql_ref", tuple(item.sql_ref for item in ordered))
        _require_unique(
            "decision_ref", tuple(item.decision.decision_ref for item in ordered)
        )
        _require_unique(
            "revision_ref", tuple(item.revision.revision_ref for item in ordered)
        )
        for previous, current in zip(ordered, ordered[1:]):
            if (
                current.base_lineage_digest_sha256
                != previous.resulting_lineage.lineage_digest
            ):
                raise SpecialistCapabilityGrowthDurableHistoryError(
                    "each entry must continue the preceding resulting lineage"
                )
            if current.revision.parent_revision_ref != previous.revision.revision_ref:
                raise SpecialistCapabilityGrowthDurableHistoryError(
                    "each recorded revision must extend the preceding revision"
                )
        object.__setattr__(self, "entries", ordered)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def latest_entry(self) -> SpecialistCapabilityGrowthHistoryEntry:
        return self.entries[-1]

    @property
    def latest_lineage(self) -> SpecialistRevisionLineage:
        return self.latest_entry.resulting_lineage

    @property
    def snapshot_digest(self) -> str:
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
            "history_ref": self.history_ref,
            "specialist_ref": self.specialist_ref,
            "entries": [item.to_mapping() for item in self.entries],
            "latest_lineage_digest": self.latest_lineage.lineage_digest,
            "metadata": dict(self.metadata),
            "append_only": True,
            "sql_authoritative": True,
            "qdrant_is_projection_only": True,
            "scheduler_revision_selection_external": True,
        }
        if include_digest:
            mapping["snapshot_digest"] = self.snapshot_digest
        return mapping


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthHistoryAppendCommand:
    """Optimistic append request bound to one approved decision and base lineage."""

    schema: str
    history_ref: str
    entry_ref: str
    sql_ref: str
    base_lineage: SpecialistRevisionLineage
    candidate_revision: PortableSpecialistRevision
    decision: SpecialistCapabilityGrowthDecision
    expected_entry_count: int
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_COMMAND_SCHEMA:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "unsupported specialist capability growth history append command schema"
            )
        _require_typed_ref(
            "history_ref", self.history_ref, required_prefixes=_HISTORY_PREFIXES
        )
        _require_typed_ref(
            "entry_ref", self.entry_ref, required_prefixes=_HISTORY_ENTRY_PREFIXES
        )
        _require_typed_ref("sql_ref", self.sql_ref, required_prefixes=_SQL_PREFIXES)
        if not isinstance(self.base_lineage, SpecialistRevisionLineage):
            raise TypeError("base_lineage must be SpecialistRevisionLineage")
        if not isinstance(self.candidate_revision, PortableSpecialistRevision):
            raise TypeError("candidate_revision must be PortableSpecialistRevision")
        if not isinstance(self.decision, SpecialistCapabilityGrowthDecision):
            raise TypeError("decision must be SpecialistCapabilityGrowthDecision")
        _require_non_negative_integer("expected_entry_count", self.expected_entry_count)
        _validate_approved_append(
            self.base_lineage,
            self.candidate_revision,
            self.decision,
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def specialist_ref(self) -> str:
        return self.candidate_revision.specialist_ref

    @property
    def command_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def build_entry(self, *, sequence_number: int) -> SpecialistCapabilityGrowthHistoryEntry:
        resulting_lineage = self.base_lineage.append(self.candidate_revision)
        return SpecialistCapabilityGrowthHistoryEntry(
            schema=SPECIALIST_CAPABILITY_GROWTH_HISTORY_ENTRY_SCHEMA,
            history_ref=self.history_ref,
            entry_ref=self.entry_ref,
            sql_ref=self.sql_ref,
            sequence_number=sequence_number,
            base_lineage_digest_sha256=self.base_lineage.lineage_digest,
            decision=self.decision,
            revision=self.candidate_revision,
            resulting_lineage=resulting_lineage,
            metadata=self.metadata,
        )

    def to_mapping(self, *, include_digest: bool = True) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "history_ref": self.history_ref,
            "entry_ref": self.entry_ref,
            "sql_ref": self.sql_ref,
            "specialist_ref": self.specialist_ref,
            "base_lineage_digest": self.base_lineage.lineage_digest,
            "candidate_revision_digest": self.candidate_revision.revision_digest,
            "decision_digest": self.decision.decision_digest,
            "expected_entry_count": self.expected_entry_count,
            "metadata": dict(self.metadata),
            "requires_operator_approval": True,
            "sql_authoritative_destination": True,
            "scheduler_selection_requested": False,
        }
        if include_digest:
            mapping["command_digest"] = self.command_digest
        return mapping


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthHistoryAppendResult:
    """Result of one port append attempt."""

    schema: str
    entry: SpecialistCapabilityGrowthHistoryEntry
    snapshot: SpecialistCapabilityGrowthHistorySnapshot
    inserted: bool
    adapter_kind: str
    durable_write_performed: bool

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_RESULT_SCHEMA:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "unsupported specialist capability growth history append result schema"
            )
        if not isinstance(self.entry, SpecialistCapabilityGrowthHistoryEntry):
            raise TypeError("entry must be SpecialistCapabilityGrowthHistoryEntry")
        if not isinstance(self.snapshot, SpecialistCapabilityGrowthHistorySnapshot):
            raise TypeError("snapshot must be SpecialistCapabilityGrowthHistorySnapshot")
        entry_refs = tuple(item.entry_ref for item in self.snapshot.entries)
        if self.entry.entry_ref not in entry_refs:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "append result entry must belong to the snapshot"
            )
        if self.inserted and self.snapshot.latest_entry.entry_ref != self.entry.entry_ref:
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "inserted append result entry must be the snapshot latest entry"
            )
        if not isinstance(self.adapter_kind, str) or not self.adapter_kind.strip():
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "adapter_kind must be non-empty"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "entry": self.entry.to_mapping(),
            "snapshot": self.snapshot.to_mapping(),
            "inserted": self.inserted,
            "adapter_kind": self.adapter_kind,
            "durable_write_performed": self.durable_write_performed,
            "authority_contract": "sql",
            "qdrant_write_performed": False,
            "scheduler_selection_performed": False,
            "scheduler_dispatch_performed": False,
            "laboratory_execution_performed": False,
            "eventbus_observation_published": False,
            "github_mutation_performed": False,
        }


@runtime_checkable
class SpecialistCapabilityGrowthHistoryPort(Protocol):
    """Boundary implemented by SQL-backed history adapters in later phases."""

    @property
    def authority_contract(self) -> str:
        """Return ``sql`` for the authoritative history destination."""

    @property
    def durable(self) -> bool:
        """Whether this adapter actually performs durable writes."""

    def append(
        self, command: SpecialistCapabilityGrowthHistoryAppendCommand
    ) -> SpecialistCapabilityGrowthHistoryAppendResult:
        """Append one approved revision with optimistic concurrency."""

    def load(
        self, history_ref: str
    ) -> SpecialistCapabilityGrowthHistorySnapshot | None:
        """Load one complete append-only history snapshot."""


class DeterministicSpecialistCapabilityGrowthHistoryAdapter:
    """Deterministic, in-memory, test-only implementation of the history port."""

    def __init__(self) -> None:
        self._snapshots: dict[str, SpecialistCapabilityGrowthHistorySnapshot] = {}

    @property
    def authority_contract(self) -> str:
        return "sql"

    @property
    def durable(self) -> bool:
        return False

    def append(
        self, command: SpecialistCapabilityGrowthHistoryAppendCommand
    ) -> SpecialistCapabilityGrowthHistoryAppendResult:
        if not isinstance(command, SpecialistCapabilityGrowthHistoryAppendCommand):
            raise TypeError(
                "command must be SpecialistCapabilityGrowthHistoryAppendCommand"
            )
        existing = self._snapshots.get(command.history_ref)

        if existing is not None:
            for entry in existing.entries:
                if entry.entry_ref == command.entry_ref:
                    candidate = command.build_entry(
                        sequence_number=entry.sequence_number
                    )
                    if candidate.entry_digest != entry.entry_digest:
                        raise SpecialistCapabilityGrowthHistoryConflictError(
                            "entry_ref already exists with different content"
                        )
                    return SpecialistCapabilityGrowthHistoryAppendResult(
                        schema=SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_RESULT_SCHEMA,
                        entry=entry,
                        snapshot=existing,
                        inserted=False,
                        adapter_kind="deterministic_test_memory",
                        durable_write_performed=False,
                    )

        if existing is not None:
            for entry in existing.entries:
                if entry.sql_ref == command.sql_ref:
                    raise SpecialistCapabilityGrowthHistoryConflictError(
                        "sql_ref already exists in append-only history"
                    )
                if entry.decision.decision_ref == command.decision.decision_ref:
                    raise SpecialistCapabilityGrowthHistoryConflictError(
                        "decision_ref already exists in append-only history"
                    )
                if entry.revision.revision_ref == command.candidate_revision.revision_ref:
                    raise SpecialistCapabilityGrowthHistoryConflictError(
                        "revision_ref already exists in append-only history"
                    )

        current_count = 0 if existing is None else len(existing.entries)
        if command.expected_entry_count != current_count:
            raise SpecialistCapabilityGrowthHistoryConflictError(
                "expected_entry_count does not match current append-only history"
            )
        if existing is not None:
            if existing.specialist_ref != command.specialist_ref:
                raise SpecialistCapabilityGrowthHistoryConflictError(
                    "history_ref already belongs to another specialist"
                )
            if existing.latest_lineage.lineage_digest != command.base_lineage.lineage_digest:
                raise SpecialistCapabilityGrowthHistoryConflictError(
                    "base lineage does not match current durable history head"
                )

        entry = command.build_entry(sequence_number=current_count + 1)
        entries = (entry,) if existing is None else (*existing.entries, entry)
        snapshot = SpecialistCapabilityGrowthHistorySnapshot(
            schema=SPECIALIST_CAPABILITY_GROWTH_HISTORY_SNAPSHOT_SCHEMA,
            history_ref=command.history_ref,
            specialist_ref=command.specialist_ref,
            entries=entries,
            metadata=() if existing is None else existing.metadata,
        )
        self._snapshots[command.history_ref] = snapshot
        return SpecialistCapabilityGrowthHistoryAppendResult(
            schema=SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_RESULT_SCHEMA,
            entry=entry,
            snapshot=snapshot,
            inserted=True,
            adapter_kind="deterministic_test_memory",
            durable_write_performed=False,
        )

    def load(
        self, history_ref: str
    ) -> SpecialistCapabilityGrowthHistorySnapshot | None:
        _require_typed_ref(
            "history_ref", history_ref, required_prefixes=_HISTORY_PREFIXES
        )
        return self._snapshots.get(history_ref)


def _validate_approved_append(
    base_lineage: SpecialistRevisionLineage,
    candidate_revision: PortableSpecialistRevision,
    decision: SpecialistCapabilityGrowthDecision,
) -> None:
    if not decision.revision_authorized:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            "append command requires an operator-approved decision"
        )
    if decision.base_lineage_ref != base_lineage.lineage_ref:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            "decision base lineage ref must match append base lineage"
        )
    if decision.base_lineage_digest_sha256 != base_lineage.lineage_digest:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            "decision base lineage digest must match append base lineage"
        )
    if decision.candidate_revision_ref != candidate_revision.revision_ref:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            "decision candidate revision ref must match append revision"
        )
    if decision.candidate_revision_digest_sha256 != candidate_revision.revision_digest:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            "decision candidate revision digest must match append revision"
        )
    if decision.specialist_ref != base_lineage.specialist_ref:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            "decision specialist_ref must match append base lineage"
        )
    if candidate_revision.specialist_ref != base_lineage.specialist_ref:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            "candidate revision specialist_ref must match append base lineage"
        )
    if candidate_revision.parent_revision_ref != base_lineage.head_revision_ref:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            "candidate revision must extend append base lineage head"
        )
    if candidate_revision.revision_number != len(base_lineage.revisions) + 1:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            "candidate revision number must follow append base lineage"
        )


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefixes: tuple[str, ...] | None = None,
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthDurableHistoryError(
            f"{name} must be a typed reference"
        )
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise SpecialistCapabilityGrowthDurableHistoryError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_sha256(name: str, value: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthDurableHistoryError(
            f"{name} must be a lowercase SHA-256 digest"
        )


def _require_positive_integer(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            f"{name} must be a positive integer"
        )


def _require_non_negative_integer(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SpecialistCapabilityGrowthDurableHistoryError(
            f"{name} must be a non-negative integer"
        )


def _require_unique(name: str, values: tuple[str, ...]) -> None:
    if len(set(values)) != len(values):
        raise SpecialistCapabilityGrowthDurableHistoryError(
            f"{name} values must be unique"
        )


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        if not isinstance(key, str) or not key.strip():
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "metadata key must be non-empty"
            )
        if not isinstance(value, str) or not value.strip():
            raise SpecialistCapabilityGrowthDurableHistoryError(
                "metadata value must be non-empty"
            )
        normalized[key.strip()] = value.strip()
    return tuple(sorted(normalized.items()))


__all__ = (
    "SPECIALIST_CAPABILITY_GROWTH_DURABLE_HISTORY_CONTRACT_VERSION",
    "SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_COMMAND_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_HISTORY_APPEND_RESULT_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_HISTORY_ENTRY_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_HISTORY_SNAPSHOT_SCHEMA",
    "DeterministicSpecialistCapabilityGrowthHistoryAdapter",
    "SpecialistCapabilityGrowthDurableHistoryError",
    "SpecialistCapabilityGrowthHistoryAppendCommand",
    "SpecialistCapabilityGrowthHistoryAppendResult",
    "SpecialistCapabilityGrowthHistoryConflictError",
    "SpecialistCapabilityGrowthHistoryEntry",
    "SpecialistCapabilityGrowthHistoryPort",
    "SpecialistCapabilityGrowthHistorySnapshot",
)
