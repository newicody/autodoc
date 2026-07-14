"""Passive EventBus and PassiveSupervisor projection for specialist growth.

Phase 0285-r7 observes the approved-revision selection produced by 0285-r6.  It
publishes immutable facts through the existing EventBus and derives an immutable
PassiveSupervisor read model.  Observation never authorizes a revision, selects a
specialist, dispatches a laboratory, or writes SQL/Qdrant.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from contracts.event import Event, EventType
from context.scheduler_approved_specialist_revision_selection_0285 import (
    SchedulerApprovedSpecialistRevisionSelectionResult,
)

SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_FACT_SCHEMA = (
    "missipy.specialist.capability_growth_observation_fact.v1"
)
SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_SCHEMA = (
    "missipy.specialist.capability_growth_observation_projection.v1"
)
SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PUBLICATION_SCHEMA = (
    "missipy.specialist.capability_growth_observation_publication.v1"
)
SPECIALIST_CAPABILITY_GROWTH_PASSIVE_READ_MODEL_SCHEMA = (
    "missipy.specialist.capability_growth_passive_read_model.v1"
)
SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_CONTRACT_VERSION = "0285.r7"

_FACT_KINDS = (
    "specialist_capability_growth.revision_proposed",
    "specialist_capability_growth.operator_approved",
    "specialist_capability_growth.durable_history_recorded",
    "specialist_capability_growth.scheduler_selected",
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SpecialistCapabilityGrowthObservationProjectionError(ValueError):
    """Raised when a passive growth observation is incoherent."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthObservationFact:
    """One immutable observation-only fact derived from the r6 selection."""

    schema: str
    fact_ref: str
    fact_kind: str
    specialist_ref: str
    revision_ref: str
    proposal_ref: str
    decision_ref: str
    history_entry_ref: str
    sql_ref: str
    selection_ref: str
    payload: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    observation_only: bool = field(default=True, init=False)
    command: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_FACT_SCHEMA:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "unsupported specialist capability growth observation fact schema"
            )
        _require_ref("fact_ref", self.fact_ref, prefixes=("observation-fact:",))
        if self.fact_kind not in _FACT_KINDS:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "unsupported specialist capability growth fact_kind"
            )
        _require_ref(
            "specialist_ref", self.specialist_ref, prefixes=("specialist:", "llm:")
        )
        _require_ref("revision_ref", self.revision_ref, prefixes=("revision:",))
        _require_ref("proposal_ref", self.proposal_ref, prefixes=("proposal:",))
        _require_ref("decision_ref", self.decision_ref, prefixes=("decision:",))
        _require_ref(
            "history_entry_ref", self.history_entry_ref, prefixes=("history-entry:",)
        )
        _require_ref("sql_ref", self.sql_ref, prefixes=("sql:",))
        _require_ref("selection_ref", self.selection_ref, prefixes=("selection:",))
        object.__setattr__(self, "payload", _normalize_metadata(self.payload))

    @property
    def fact_digest(self) -> str:
        return _digest(self.to_mapping(include_digest=False))

    def to_mapping(self, *, include_digest: bool = True) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "fact_ref": self.fact_ref,
            "fact_kind": self.fact_kind,
            "specialist_ref": self.specialist_ref,
            "revision_ref": self.revision_ref,
            "proposal_ref": self.proposal_ref,
            "decision_ref": self.decision_ref,
            "history_entry_ref": self.history_entry_ref,
            "sql_ref": self.sql_ref,
            "selection_ref": self.selection_ref,
            "payload": dict(self.payload),
            "observation_only": self.observation_only,
            "command": self.command,
        }
        if include_digest:
            mapping["fact_digest"] = self.fact_digest
        return mapping


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthObservationProjection:
    """Correlated facts ready for publication on the existing EventBus."""

    schema: str
    selection_ref: str
    selection_digest_sha256: str
    specialist_ref: str
    revision_ref: str
    proposal_ref: str
    decision_ref: str
    history_entry_ref: str
    sql_ref: str
    facts: tuple[SpecialistCapabilityGrowthObservationFact, ...]
    observation_only: bool = field(default=True, init=False)
    authoritative: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_SCHEMA:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "unsupported specialist capability growth observation projection schema"
            )
        _require_ref("selection_ref", self.selection_ref, prefixes=("selection:",))
        _require_sha256("selection_digest_sha256", self.selection_digest_sha256)
        _require_ref(
            "specialist_ref", self.specialist_ref, prefixes=("specialist:", "llm:")
        )
        _require_ref("revision_ref", self.revision_ref, prefixes=("revision:",))
        _require_ref("proposal_ref", self.proposal_ref, prefixes=("proposal:",))
        _require_ref("decision_ref", self.decision_ref, prefixes=("decision:",))
        _require_ref(
            "history_entry_ref", self.history_entry_ref, prefixes=("history-entry:",)
        )
        _require_ref("sql_ref", self.sql_ref, prefixes=("sql:",))
        facts = tuple(self.facts)
        if len(facts) != len(_FACT_KINDS):
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "projection must contain the four canonical growth facts"
            )
        if not all(
            isinstance(item, SpecialistCapabilityGrowthObservationFact)
            for item in facts
        ):
            raise TypeError("facts must contain SpecialistCapabilityGrowthObservationFact")
        if tuple(item.fact_kind for item in facts) != _FACT_KINDS:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "projection facts must follow the canonical deterministic order"
            )
        for fact in facts:
            if (
                fact.specialist_ref != self.specialist_ref
                or fact.revision_ref != self.revision_ref
                or fact.proposal_ref != self.proposal_ref
                or fact.decision_ref != self.decision_ref
                or fact.history_entry_ref != self.history_entry_ref
                or fact.sql_ref != self.sql_ref
                or fact.selection_ref != self.selection_ref
            ):
                raise SpecialistCapabilityGrowthObservationProjectionError(
                    "all observation facts must preserve projection correlation"
                )
        object.__setattr__(self, "facts", facts)

    @property
    def projection_digest(self) -> str:
        return _digest(self.to_mapping(include_digest=False))

    def to_mapping(self, *, include_digest: bool = True) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "selection_ref": self.selection_ref,
            "selection_digest_sha256": self.selection_digest_sha256,
            "specialist_ref": self.specialist_ref,
            "revision_ref": self.revision_ref,
            "proposal_ref": self.proposal_ref,
            "decision_ref": self.decision_ref,
            "history_entry_ref": self.history_entry_ref,
            "sql_ref": self.sql_ref,
            "facts": [item.to_mapping() for item in self.facts],
            "observation_only": self.observation_only,
            "authoritative": self.authoritative,
            "scheduler_selection_performed": True,
            "scheduler_dispatch_performed": False,
            "laboratory_execution_performed": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
        }
        if include_digest:
            mapping["projection_digest"] = self.projection_digest
        return mapping


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthObservationPublicationReport:
    """Result of publishing one passive projection through the existing EventBus."""

    schema: str
    projection: SpecialistCapabilityGrowthObservationProjection
    event_id: str
    event_type: str
    published_count: int
    eventbus_observation_only: bool = field(default=True, init=False)
    controls_execution: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PUBLICATION_SCHEMA:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "unsupported observation publication schema"
            )
        if not isinstance(
            self.projection, SpecialistCapabilityGrowthObservationProjection
        ):
            raise TypeError("projection must be SpecialistCapabilityGrowthObservationProjection")
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "event_id must be non-empty"
            )
        if self.event_type != EventType.SPECIALIST_REVISION_SELECTION_RESULT.name:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "publication must use SPECIALIST_REVISION_SELECTION_RESULT"
            )
        if self.published_count != 1:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "one projection publication must publish exactly one event"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "projection": self.projection.to_mapping(),
            "event_id": self.event_id,
            "event_type": self.event_type,
            "published_count": self.published_count,
            "eventbus_observation_only": self.eventbus_observation_only,
            "controls_execution": self.controls_execution,
        }


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthPassiveFinding:
    """One passive finding derived from an already-published observation fact."""

    finding_ref: str
    fact_ref: str
    fact_kind: str
    severity: str
    message: str
    observation_only: bool = field(default=True, init=False)
    command: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        _require_ref("finding_ref", self.finding_ref, prefixes=("passive-finding:",))
        _require_ref("fact_ref", self.fact_ref, prefixes=("observation-fact:",))
        if self.fact_kind not in _FACT_KINDS:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "unsupported passive finding fact_kind"
            )
        if self.severity not in {"info", "warning", "error"}:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "unsupported passive finding severity"
            )
        if not isinstance(self.message, str) or not self.message.strip():
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "passive finding message must be non-empty"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "finding_ref": self.finding_ref,
            "fact_ref": self.fact_ref,
            "fact_kind": self.fact_kind,
            "severity": self.severity,
            "message": self.message,
            "observation_only": self.observation_only,
            "command": self.command,
        }


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthPassiveReadModel:
    """Immutable PassiveSupervisor view; it cannot influence the selected revision."""

    schema: str
    source_event_id: str
    source_event_type: str
    selection_ref: str
    specialist_ref: str
    revision_ref: str
    proposal_ref: str
    decision_ref: str
    history_entry_ref: str
    sql_ref: str
    findings: tuple[SpecialistCapabilityGrowthPassiveFinding, ...]
    accepted_fact_count: int
    rejected_fact_count: int
    passive_supervisor_observation_only: bool = field(default=True, init=False)
    authoritative: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_PASSIVE_READ_MODEL_SCHEMA:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "unsupported specialist capability growth passive read-model schema"
            )
        if not isinstance(self.source_event_id, str) or not self.source_event_id.strip():
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "source_event_id must be non-empty"
            )
        if self.source_event_type != EventType.SPECIALIST_REVISION_SELECTION_RESULT.name:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "passive read model requires SPECIALIST_REVISION_SELECTION_RESULT"
            )
        _require_ref("selection_ref", self.selection_ref, prefixes=("selection:",))
        _require_ref(
            "specialist_ref", self.specialist_ref, prefixes=("specialist:", "llm:")
        )
        _require_ref("revision_ref", self.revision_ref, prefixes=("revision:",))
        _require_ref("proposal_ref", self.proposal_ref, prefixes=("proposal:",))
        _require_ref("decision_ref", self.decision_ref, prefixes=("decision:",))
        _require_ref(
            "history_entry_ref", self.history_entry_ref, prefixes=("history-entry:",)
        )
        _require_ref("sql_ref", self.sql_ref, prefixes=("sql:",))
        findings = tuple(self.findings)
        if not all(
            isinstance(item, SpecialistCapabilityGrowthPassiveFinding)
            for item in findings
        ):
            raise TypeError("findings must contain passive findings")
        if self.accepted_fact_count + self.rejected_fact_count != len(findings):
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "passive finding counters must match findings"
            )
        object.__setattr__(self, "findings", findings)

    @property
    def valid(self) -> bool:
        return self.rejected_fact_count == 0

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "source_event_id": self.source_event_id,
            "source_event_type": self.source_event_type,
            "selection_ref": self.selection_ref,
            "specialist_ref": self.specialist_ref,
            "revision_ref": self.revision_ref,
            "proposal_ref": self.proposal_ref,
            "decision_ref": self.decision_ref,
            "history_entry_ref": self.history_entry_ref,
            "sql_ref": self.sql_ref,
            "findings": [item.to_mapping() for item in self.findings],
            "accepted_fact_count": self.accepted_fact_count,
            "rejected_fact_count": self.rejected_fact_count,
            "valid": self.valid,
            "passive_supervisor_observation_only": (
                self.passive_supervisor_observation_only
            ),
            "authoritative": self.authoritative,
            "can_authorize_revision": False,
            "can_select_revision": False,
            "can_dispatch_laboratory": False,
            "can_write_sql": False,
            "can_write_qdrant": False,
        }


@runtime_checkable
class SpecialistCapabilityGrowthObservationEventBusPort(Protocol):
    """Minimal observation port already implemented by kernel.event_bus.EventBus."""

    async def publish(self, event: Event) -> None:
        """Publish one observation event without controlling execution."""


def build_specialist_capability_growth_observation_projection(
    selection: SchedulerApprovedSpecialistRevisionSelectionResult,
) -> SpecialistCapabilityGrowthObservationProjection:
    """Build four deterministic facts from one safe r6 selection result."""

    _validate_selection(selection)
    revision = selection.selected_revision
    proposal_ref = revision.source_proposal_ref
    assert proposal_ref is not None
    shared = {
        "specialist_ref": selection.specialist_ref,
        "revision_ref": revision.revision_ref,
        "proposal_ref": proposal_ref,
        "decision_ref": selection.decision_ref,
        "history_entry_ref": selection.history_entry_ref,
        "sql_ref": selection.sql_ref,
        "selection_ref": selection.selection_ref,
    }
    fact_specs = (
        (
            _FACT_KINDS[0],
            (
                ("proposal_digest_sha256", revision.source_proposal_digest_sha256 or ""),
                ("revision_digest_sha256", revision.revision_digest),
                ("evidence_count", str(len(revision.evidence_refs))),
            ),
        ),
        (
            _FACT_KINDS[1],
            (
                ("policy_ref", selection.policy_ref),
                ("policy_digest_sha256", selection.policy_digest_sha256),
                ("operator_decision_authoritative", "true"),
            ),
        ),
        (
            _FACT_KINDS[2],
            (
                ("history_ref", selection.history_ref),
                (
                    "history_snapshot_digest_sha256",
                    selection.history_snapshot_digest_sha256,
                ),
                ("history_entry_digest_sha256", selection.history_entry_digest_sha256),
                ("sql_is_durable_authority", "true"),
            ),
        ),
        (
            _FACT_KINDS[3],
            (
                ("scheduler_ref", selection.scheduler_ref),
                ("capability", selection.capability),
                ("laboratory_ref", selection.laboratory_ref),
                ("visit_mode", selection.visit_mode),
                ("execution_boundary", selection.execution_boundary),
                ("laboratory_dispatch_performed", "false"),
            ),
        ),
    )
    facts = tuple(
        SpecialistCapabilityGrowthObservationFact(
            schema=SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_FACT_SCHEMA,
            fact_ref=(
                f"observation-fact:0285-r7:{selection.selection_ref}:"
                f"{fact_kind.rsplit('.', 1)[-1]}"
            ),
            fact_kind=fact_kind,
            payload=payload,
            **shared,
        )
        for fact_kind, payload in fact_specs
    )
    return SpecialistCapabilityGrowthObservationProjection(
        schema=SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_SCHEMA,
        selection_ref=selection.selection_ref,
        selection_digest_sha256=selection.selection_digest,
        specialist_ref=selection.specialist_ref,
        revision_ref=revision.revision_ref,
        proposal_ref=proposal_ref,
        decision_ref=selection.decision_ref,
        history_entry_ref=selection.history_entry_ref,
        sql_ref=selection.sql_ref,
        facts=facts,
    )


def build_specialist_capability_growth_observation_event(
    projection: SpecialistCapabilityGrowthObservationProjection,
    *,
    event_id: str | None = None,
) -> Event:
    """Wrap a passive projection in the result event reserved by 0285-r6."""

    if not isinstance(projection, SpecialistCapabilityGrowthObservationProjection):
        raise TypeError("projection must be SpecialistCapabilityGrowthObservationProjection")
    metadata = MappingProxyType(
        {
            "observation_only": True,
            "command": False,
            "specialist_ref": projection.specialist_ref,
            "revision_ref": projection.revision_ref,
            "proposal_ref": projection.proposal_ref,
            "decision_ref": projection.decision_ref,
            "history_entry_ref": projection.history_entry_ref,
            "sql_ref": projection.sql_ref,
            "selection_ref": projection.selection_ref,
            "projection_digest_sha256": projection.projection_digest,
            "source_class": "specialist-capability-growth-observation",
            "lifecycle_state": "completed",
        }
    )
    kwargs: dict[str, object] = {
        "type": EventType.SPECIALIST_REVISION_SELECTION_RESULT,
        "source": "scheduler-approved-specialist-revision-selection-0285-r6",
        "dest": "observability",
        "payload": projection,
        "correlation_id": projection.selection_ref,
        "metadata": metadata,
    }
    if event_id is not None:
        if not isinstance(event_id, str) or not event_id.strip():
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "event_id must be non-empty when supplied"
            )
        kwargs["id"] = event_id
    return Event(**kwargs)


async def publish_specialist_capability_growth_observation(
    event_bus: SpecialistCapabilityGrowthObservationEventBusPort,
    selection: SchedulerApprovedSpecialistRevisionSelectionResult,
    *,
    event_id: str | None = None,
) -> SpecialistCapabilityGrowthObservationPublicationReport:
    """Publish one observation event through the existing EventBus port."""

    if not isinstance(event_bus, SpecialistCapabilityGrowthObservationEventBusPort):
        raise TypeError("event_bus must implement the observation publish port")
    projection = build_specialist_capability_growth_observation_projection(selection)
    event = build_specialist_capability_growth_observation_event(
        projection, event_id=event_id
    )
    await event_bus.publish(event)
    return SpecialistCapabilityGrowthObservationPublicationReport(
        schema=SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PUBLICATION_SCHEMA,
        projection=projection,
        event_id=event.id,
        event_type=event.type.name,
        published_count=1,
    )


def build_specialist_capability_growth_passive_read_model(
    event: Event,
) -> SpecialistCapabilityGrowthPassiveReadModel:
    """Derive a PassiveSupervisor view from one already-emitted observation event."""

    if not isinstance(event, Event):
        raise TypeError("event must be Event")
    if event.type is not EventType.SPECIALIST_REVISION_SELECTION_RESULT:
        raise SpecialistCapabilityGrowthObservationProjectionError(
            "passive read model only accepts SPECIALIST_REVISION_SELECTION_RESULT"
        )
    if not isinstance(event.payload, SpecialistCapabilityGrowthObservationProjection):
        raise TypeError("event payload must be a growth observation projection")
    if event.dest != "observability":
        raise SpecialistCapabilityGrowthObservationProjectionError(
            "growth observation event must target observability"
        )
    projection = event.payload
    findings: list[SpecialistCapabilityGrowthPassiveFinding] = []
    for index, fact in enumerate(projection.facts):
        accepted = fact.observation_only and not fact.command
        findings.append(
            SpecialistCapabilityGrowthPassiveFinding(
                finding_ref=(
                    f"passive-finding:0285-r7:{projection.selection_ref}:{index}"
                ),
                fact_ref=fact.fact_ref,
                fact_kind=fact.fact_kind,
                severity="info" if accepted else "error",
                message=(
                    "Observation fact accepted by PassiveSupervisor"
                    if accepted
                    else "Observation fact rejected as command-like"
                ),
            )
        )
    rejected = sum(item.severity == "error" for item in findings)
    return SpecialistCapabilityGrowthPassiveReadModel(
        schema=SPECIALIST_CAPABILITY_GROWTH_PASSIVE_READ_MODEL_SCHEMA,
        source_event_id=event.id,
        source_event_type=event.type.name,
        selection_ref=projection.selection_ref,
        specialist_ref=projection.specialist_ref,
        revision_ref=projection.revision_ref,
        proposal_ref=projection.proposal_ref,
        decision_ref=projection.decision_ref,
        history_entry_ref=projection.history_entry_ref,
        sql_ref=projection.sql_ref,
        findings=tuple(findings),
        accepted_fact_count=len(findings) - rejected,
        rejected_fact_count=rejected,
    )


def _validate_selection(
    selection: SchedulerApprovedSpecialistRevisionSelectionResult,
) -> None:
    if not isinstance(selection, SchedulerApprovedSpecialistRevisionSelectionResult):
        raise TypeError(
            "selection must be SchedulerApprovedSpecialistRevisionSelectionResult"
        )
    revision = selection.selected_revision
    proposal_ref = revision.source_proposal_ref
    if not isinstance(proposal_ref, str) or not proposal_ref.startswith("proposal:"):
        raise SpecialistCapabilityGrowthObservationProjectionError(
            "growth observation requires a non-root revision with source proposal"
        )
    _require_sha256("selection_digest", selection.selection_digest)
    _require_sha256("revision_digest", revision.revision_digest)
    _require_sha256(
        "source_proposal_digest_sha256", revision.source_proposal_digest_sha256
    )
    mapping = selection.to_mapping()
    required_boundaries = {
        "scheduler_selection_performed": True,
        "scheduler_dispatch_performed": False,
        "laboratory_execution_performed": False,
        "sql_write_performed": False,
        "qdrant_write_performed": False,
        "eventbus_observation_published": False,
        "github_mutation_performed": False,
        "new_scheduler_created": False,
        "parallel_orchestrator_created": False,
    }
    for name, expected in required_boundaries.items():
        if mapping.get(name) is not expected:
            raise SpecialistCapabilityGrowthObservationProjectionError(
                f"unsafe r6 selection boundary: {name}"
            )


def _require_ref(name: str, value: str, *, prefixes: tuple[str, ...]) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthObservationProjectionError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(prefixes):
        raise SpecialistCapabilityGrowthObservationProjectionError(
            f"{name} must start with one of: {', '.join(prefixes)}"
        )


def _require_sha256(name: str, value: str | None) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthObservationProjectionError(
            f"{name} must be a lowercase SHA-256 digest"
        )


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        if not isinstance(key, str) or not key.strip():
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "payload key must be non-empty"
            )
        if not isinstance(value, str) or not value.strip():
            raise SpecialistCapabilityGrowthObservationProjectionError(
                "payload value must be non-empty"
            )
        normalized[key.strip()] = value.strip()
    return tuple(sorted(normalized.items()))


def _digest(mapping: Mapping[str, object]) -> str:
    payload = json.dumps(
        dict(mapping), ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return sha256(payload).hexdigest()


__all__ = (
    "SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_CONTRACT_VERSION",
    "SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_FACT_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PUBLICATION_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_PASSIVE_READ_MODEL_SCHEMA",
    "SpecialistCapabilityGrowthObservationEventBusPort",
    "SpecialistCapabilityGrowthObservationFact",
    "SpecialistCapabilityGrowthObservationProjection",
    "SpecialistCapabilityGrowthObservationProjectionError",
    "SpecialistCapabilityGrowthObservationPublicationReport",
    "SpecialistCapabilityGrowthPassiveFinding",
    "SpecialistCapabilityGrowthPassiveReadModel",
    "build_specialist_capability_growth_observation_event",
    "build_specialist_capability_growth_observation_projection",
    "build_specialist_capability_growth_passive_read_model",
    "publish_specialist_capability_growth_observation",
)
