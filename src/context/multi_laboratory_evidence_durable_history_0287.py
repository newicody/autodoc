"""Append-only SQL-authority history for multi-laboratory evidence.

Only operator-approved r6 weighting decisions may enter this history. The
included adapter is deterministic, in-memory and test-only; real persistence
belongs behind ``MultiLaboratoryEvidenceHistoryPort``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Protocol, runtime_checkable

from context.multi_laboratory_evidence_operator_weighting_policy_0287 import (
    MultiLaboratoryEvidenceWeightingDecision,
)


MULTI_LABORATORY_EVIDENCE_HISTORY_APPEND_COMMAND_SCHEMA = (
    "missipy.multi_laboratory.evidence_history_append_command.v1"
)
MULTI_LABORATORY_EVIDENCE_HISTORY_ENTRY_SCHEMA = (
    "missipy.multi_laboratory.evidence_history_entry.v1"
)
MULTI_LABORATORY_EVIDENCE_HISTORY_SNAPSHOT_SCHEMA = (
    "missipy.multi_laboratory.evidence_history_snapshot.v1"
)
MULTI_LABORATORY_EVIDENCE_HISTORY_APPEND_RESULT_SCHEMA = (
    "missipy.multi_laboratory.evidence_history_append_result.v1"
)
MULTI_LABORATORY_EVIDENCE_DURABLE_HISTORY_VERSION = "0287.r7"

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ZERO_DIGEST = "0" * 64


class MultiLaboratoryEvidenceDurableHistoryError(ValueError):
    """Raised for invalid append-only history state."""


class MultiLaboratoryEvidenceHistoryConflictError(
    MultiLaboratoryEvidenceDurableHistoryError
):
    """Raised for optimistic-concurrency or identity collisions."""


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceHistoryEntry:
    """One immutable SQL-addressed approved weighting decision."""

    schema: str
    history_ref: str
    entry_ref: str
    sql_ref: str
    sequence_number: int
    previous_entry_digest: str
    decision: MultiLaboratoryEvidenceWeightingDecision
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_HISTORY_ENTRY_SCHEMA:
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "unsupported evidence history entry schema"
            )
        _require_ref("history_ref", self.history_ref, "history:")
        _require_ref("entry_ref", self.entry_ref, "history-entry:")
        _require_ref("sql_ref", self.sql_ref, "sql:")
        _require_positive_int("sequence_number", self.sequence_number)
        _require_digest("previous_entry_digest", self.previous_entry_digest)
        if not isinstance(
            self.decision,
            MultiLaboratoryEvidenceWeightingDecision,
        ):
            raise TypeError(
                "decision must be MultiLaboratoryEvidenceWeightingDecision"
            )
        if not self.decision.weighting_authorized:
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "history entry requires an operator-approved decision"
            )
        object.__setattr__(
            self,
            "metadata",
            _normalize_metadata(self.metadata),
        )

    @property
    def aggregation_ref(self) -> str:
        return self.decision.aggregation_ref

    @property
    def entry_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_digest=False),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(
        self,
        *,
        include_digest: bool = True,
    ) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "history_ref": self.history_ref,
            "entry_ref": self.entry_ref,
            "sql_ref": self.sql_ref,
            "sequence_number": self.sequence_number,
            "previous_entry_digest": self.previous_entry_digest,
            "aggregation_ref": self.aggregation_ref,
            "decision_ref": self.decision.decision_ref,
            "weighting_digest": self.decision.weighting_digest,
            "decision": self.decision.to_mapping(),
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
class MultiLaboratoryEvidenceHistorySnapshot:
    """Validated append-only history for one aggregation."""

    schema: str
    history_ref: str
    aggregation_ref: str
    entries: tuple[MultiLaboratoryEvidenceHistoryEntry, ...]
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != MULTI_LABORATORY_EVIDENCE_HISTORY_SNAPSHOT_SCHEMA:
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "unsupported evidence history snapshot schema"
            )
        _require_ref("history_ref", self.history_ref, "history:")
        _require_ref("aggregation_ref", self.aggregation_ref, "aggregation:")
        entries = tuple(
            sorted(self.entries, key=lambda item: item.sequence_number)
        )
        if not entries:
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "snapshot must contain at least one entry"
            )
        if tuple(item.sequence_number for item in entries) != tuple(
            range(1, len(entries) + 1)
        ):
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "sequence numbers must be contiguous and start at one"
            )
        if any(item.history_ref != self.history_ref for item in entries):
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "entries must preserve history_ref"
            )
        if any(
            item.aggregation_ref != self.aggregation_ref
            for item in entries
        ):
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "entries must preserve aggregation_ref"
            )
        _require_unique("entry_ref", tuple(item.entry_ref for item in entries))
        _require_unique("sql_ref", tuple(item.sql_ref for item in entries))
        _require_unique(
            "decision_ref",
            tuple(item.decision.decision_ref for item in entries),
        )
        _require_unique(
            "weighting_digest",
            tuple(item.decision.weighting_digest for item in entries),
        )
        if entries[0].previous_entry_digest != _ZERO_DIGEST:
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "first entry must use the zero previous digest"
            )
        for previous, entry in zip(entries, entries[1:]):
            if entry.previous_entry_digest != previous.entry_digest:
                raise MultiLaboratoryEvidenceDurableHistoryError(
                    "history digest chain mismatch"
                )
        object.__setattr__(self, "entries", entries)
        object.__setattr__(
            self,
            "metadata",
            _normalize_metadata(self.metadata),
        )

    @property
    def latest_entry(self) -> MultiLaboratoryEvidenceHistoryEntry:
        return self.entries[-1]

    @property
    def head_entry_digest(self) -> str:
        return self.latest_entry.entry_digest

    @property
    def snapshot_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_digest=False),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(
        self,
        *,
        include_digest: bool = True,
    ) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "history_ref": self.history_ref,
            "aggregation_ref": self.aggregation_ref,
            "entries": [item.to_mapping() for item in self.entries],
            "head_entry_digest": self.head_entry_digest,
            "metadata": dict(self.metadata),
            "append_only": True,
            "sql_authoritative": True,
            "qdrant_is_projection_only": True,
            "scheduler_selection_external": True,
        }
        if include_digest:
            mapping["snapshot_digest"] = self.snapshot_digest
        return mapping


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceHistoryAppendCommand:
    """Optimistic append request for one approved r6 decision."""

    schema: str
    history_ref: str
    entry_ref: str
    sql_ref: str
    decision: MultiLaboratoryEvidenceWeightingDecision
    expected_entry_count: int
    expected_head_entry_digest: str
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != (
            MULTI_LABORATORY_EVIDENCE_HISTORY_APPEND_COMMAND_SCHEMA
        ):
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "unsupported evidence history append command schema"
            )
        _require_ref("history_ref", self.history_ref, "history:")
        _require_ref("entry_ref", self.entry_ref, "history-entry:")
        _require_ref("sql_ref", self.sql_ref, "sql:")
        if not isinstance(
            self.decision,
            MultiLaboratoryEvidenceWeightingDecision,
        ):
            raise TypeError(
                "decision must be MultiLaboratoryEvidenceWeightingDecision"
            )
        if not self.decision.durable_history_append_allowed:
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "append requires an operator-approved decision"
            )
        _require_non_negative_int(
            "expected_entry_count",
            self.expected_entry_count,
        )
        _require_digest(
            "expected_head_entry_digest",
            self.expected_head_entry_digest,
        )
        if (
            self.expected_entry_count == 0
            and self.expected_head_entry_digest != _ZERO_DIGEST
        ):
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "empty history must expect the zero head digest"
            )
        object.__setattr__(
            self,
            "metadata",
            _normalize_metadata(self.metadata),
        )

    @property
    def aggregation_ref(self) -> str:
        return self.decision.aggregation_ref

    @property
    def command_digest(self) -> str:
        payload = json.dumps(
            self.to_mapping(include_digest=False),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def build_entry(
        self,
        *,
        sequence_number: int,
    ) -> MultiLaboratoryEvidenceHistoryEntry:
        return MultiLaboratoryEvidenceHistoryEntry(
            schema=MULTI_LABORATORY_EVIDENCE_HISTORY_ENTRY_SCHEMA,
            history_ref=self.history_ref,
            entry_ref=self.entry_ref,
            sql_ref=self.sql_ref,
            sequence_number=sequence_number,
            previous_entry_digest=self.expected_head_entry_digest,
            decision=self.decision,
            metadata=self.metadata,
        )

    def to_mapping(
        self,
        *,
        include_digest: bool = True,
    ) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "history_ref": self.history_ref,
            "entry_ref": self.entry_ref,
            "sql_ref": self.sql_ref,
            "aggregation_ref": self.aggregation_ref,
            "decision_ref": self.decision.decision_ref,
            "weighting_digest": self.decision.weighting_digest,
            "expected_entry_count": self.expected_entry_count,
            "expected_head_entry_digest": (
                self.expected_head_entry_digest
            ),
            "metadata": dict(self.metadata),
            "requires_operator_approval": True,
            "sql_authoritative_destination": True,
            "scheduler_selection_requested": False,
        }
        if include_digest:
            mapping["command_digest"] = self.command_digest
        return mapping


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceHistoryAppendResult:
    """Result of one append attempt."""

    schema: str
    entry: MultiLaboratoryEvidenceHistoryEntry
    snapshot: MultiLaboratoryEvidenceHistorySnapshot
    inserted: bool
    adapter_kind: str
    durable_write_performed: bool

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
class MultiLaboratoryEvidenceHistoryPort(Protocol):
    """Port implemented later by the real SQL adapter."""

    @property
    def authority_contract(self) -> str: ...

    @property
    def durable(self) -> bool: ...

    def append(
        self,
        command: MultiLaboratoryEvidenceHistoryAppendCommand,
    ) -> MultiLaboratoryEvidenceHistoryAppendResult: ...

    def load(
        self,
        history_ref: str,
    ) -> MultiLaboratoryEvidenceHistorySnapshot | None: ...


class DeterministicMultiLaboratoryEvidenceHistoryAdapter:
    """In-memory test adapter with SQL authority contract."""

    def __init__(self) -> None:
        self._snapshots: dict[
            str,
            MultiLaboratoryEvidenceHistorySnapshot,
        ] = {}

    @property
    def authority_contract(self) -> str:
        return "sql"

    @property
    def durable(self) -> bool:
        return False

    def append(
        self,
        command: MultiLaboratoryEvidenceHistoryAppendCommand,
    ) -> MultiLaboratoryEvidenceHistoryAppendResult:
        existing = self._snapshots.get(command.history_ref)
        if existing is not None:
            for entry in existing.entries:
                if entry.entry_ref == command.entry_ref:
                    candidate = command.build_entry(
                        sequence_number=entry.sequence_number
                    )
                    if candidate.entry_digest != entry.entry_digest:
                        raise MultiLaboratoryEvidenceHistoryConflictError(
                            "entry_ref already exists with different content"
                        )
                    return MultiLaboratoryEvidenceHistoryAppendResult(
                        schema=(
                            MULTI_LABORATORY_EVIDENCE_HISTORY_APPEND_RESULT_SCHEMA
                        ),
                        entry=entry,
                        snapshot=existing,
                        inserted=False,
                        adapter_kind="deterministic_test_memory",
                        durable_write_performed=False,
                    )

        count = 0 if existing is None else len(existing.entries)
        head = _ZERO_DIGEST if existing is None else existing.head_entry_digest
        if command.expected_entry_count != count:
            raise MultiLaboratoryEvidenceHistoryConflictError(
                "expected_entry_count does not match history"
            )
        if command.expected_head_entry_digest != head:
            raise MultiLaboratoryEvidenceHistoryConflictError(
                "expected head digest does not match history"
            )
        if existing is not None:
            if existing.aggregation_ref != command.aggregation_ref:
                raise MultiLaboratoryEvidenceHistoryConflictError(
                    "history_ref belongs to another aggregation"
                )
            if any(
                item.sql_ref == command.sql_ref
                for item in existing.entries
            ):
                raise MultiLaboratoryEvidenceHistoryConflictError(
                    "sql_ref already exists"
                )
            if any(
                item.decision.decision_ref == command.decision.decision_ref
                for item in existing.entries
            ):
                raise MultiLaboratoryEvidenceHistoryConflictError(
                    "decision_ref already exists"
                )
            if any(
                item.decision.weighting_digest
                == command.decision.weighting_digest
                for item in existing.entries
            ):
                raise MultiLaboratoryEvidenceHistoryConflictError(
                    "weighting_digest already exists"
                )

        entry = command.build_entry(sequence_number=count + 1)
        snapshot = MultiLaboratoryEvidenceHistorySnapshot(
            schema=MULTI_LABORATORY_EVIDENCE_HISTORY_SNAPSHOT_SCHEMA,
            history_ref=command.history_ref,
            aggregation_ref=command.aggregation_ref,
            entries=(entry,) if existing is None else (*existing.entries, entry),
            metadata=() if existing is None else existing.metadata,
        )
        self._snapshots[command.history_ref] = snapshot
        return MultiLaboratoryEvidenceHistoryAppendResult(
            schema=MULTI_LABORATORY_EVIDENCE_HISTORY_APPEND_RESULT_SCHEMA,
            entry=entry,
            snapshot=snapshot,
            inserted=True,
            adapter_kind="deterministic_test_memory",
            durable_write_performed=False,
        )

    def load(
        self,
        history_ref: str,
    ) -> MultiLaboratoryEvidenceHistorySnapshot | None:
        _require_ref("history_ref", history_ref, "history:")
        return self._snapshots.get(history_ref)


def _require_ref(name: str, value: str, prefix: str) -> None:
    if (
        not isinstance(value, str)
        or not _TYPED_REF_RE.fullmatch(value)
        or not value.startswith(prefix)
    ):
        raise MultiLaboratoryEvidenceDurableHistoryError(
            f"{name} must start with {prefix}"
        )


def _require_digest(name: str, value: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise MultiLaboratoryEvidenceDurableHistoryError(
            f"{name} must be a lowercase SHA-256"
        )


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise MultiLaboratoryEvidenceDurableHistoryError(
            f"{name} must be positive"
        )


def _require_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MultiLaboratoryEvidenceDurableHistoryError(
            f"{name} must be non-negative"
        )


def _require_unique(name: str, values: tuple[str, ...]) -> None:
    if len(values) != len(set(values)):
        raise MultiLaboratoryEvidenceDurableHistoryError(
            f"{name} values must be unique"
        )


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        if not isinstance(key, str) or not key.strip():
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "metadata key must be non-empty"
            )
        if not isinstance(value, str) or not value.strip():
            raise MultiLaboratoryEvidenceDurableHistoryError(
                "metadata value must be non-empty"
            )
        normalized[key.strip()] = value.strip()
    return tuple(sorted(normalized.items()))


__all__ = (
    "MULTI_LABORATORY_EVIDENCE_DURABLE_HISTORY_VERSION",
    "MULTI_LABORATORY_EVIDENCE_HISTORY_APPEND_COMMAND_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_HISTORY_APPEND_RESULT_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_HISTORY_ENTRY_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_HISTORY_SNAPSHOT_SCHEMA",
    "DeterministicMultiLaboratoryEvidenceHistoryAdapter",
    "MultiLaboratoryEvidenceDurableHistoryError",
    "MultiLaboratoryEvidenceHistoryAppendCommand",
    "MultiLaboratoryEvidenceHistoryAppendResult",
    "MultiLaboratoryEvidenceHistoryConflictError",
    "MultiLaboratoryEvidenceHistoryEntry",
    "MultiLaboratoryEvidenceHistoryPort",
    "MultiLaboratoryEvidenceHistorySnapshot",
)
