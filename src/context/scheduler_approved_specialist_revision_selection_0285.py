"""Scheduler-owned selection of one approved portable-specialist revision.

Phase 0285-r6 extends the existing Event -> Scheduler -> Dispatcher -> Handler path
without adding another Scheduler, registry or orchestrator.  Selection is pure: it
requires a durable SQL-authoritative r5 history result, selects only its latest
operator-approved revision, validates one laboratory route and returns an immutable
selection result.  It does not dispatch a laboratory visit or write SQL/Qdrant.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from contracts.event import Event, EventType
from context.portable_specialist_contract_0284 import (
    PortableSpecialistDescriptor,
    SpecialistCapabilityContract,
    SpecialistExecutionBoundary,
    SpecialistLaboratoryVisitMode,
)
from context.portable_specialist_revision_lineage_contract_0285 import (
    PortableSpecialistRevision,
)
from context.specialist_capability_growth_durable_history_0285 import (
    SpecialistCapabilityGrowthHistoryAppendResult,
)

SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_POLICY_SCHEMA = (
    "missipy.specialist.scheduler_approved_revision_selection_policy.v1"
)
SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_COMMAND_SCHEMA = (
    "missipy.specialist.scheduler_approved_revision_selection_command.v1"
)
SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_RESULT_SCHEMA = (
    "missipy.specialist.scheduler_approved_revision_selection_result.v1"
)
SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_CONTRACT_VERSION = "0285.r6"

_ALLOWED_VISIT_MODES = frozenset({"resident", "visitor", "transfer"})
_ALLOWED_EXECUTION_BOUNDARIES = frozenset(
    {"in_process", "local_process", "remote_service"}
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMAND_PREFIXES = ("selection-command:",)
_SELECTION_PREFIXES = ("selection:",)
_POLICY_PREFIXES = ("policy:",)
_SCHEDULER_PREFIXES = ("scheduler:",)
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_LABORATORY_PREFIXES = ("laboratory:",)
_CONTRACT_PREFIXES = ("contract:",)
_CONVERSATION_PREFIXES = ("conversation:",)
_CONTEXT_PREFIXES = ("context:", "sql:")


class SchedulerApprovedSpecialistRevisionSelectionError(ValueError):
    """Raised when an approved specialist revision cannot be selected safely."""


@dataclass(frozen=True, slots=True)
class SchedulerApprovedSpecialistRevisionSelectionPolicy:
    """Explicit Scheduler-side constraints for revision selection."""

    schema: str
    policy_ref: str
    scheduler_ref: str
    allowed_laboratory_refs: tuple[str, ...] = field(default_factory=tuple)
    allowed_visit_modes: tuple[SpecialistLaboratoryVisitMode, ...] = (
        "resident",
        "visitor",
    )
    allowed_execution_boundaries: tuple[SpecialistExecutionBoundary, ...] = (
        "in_process",
        "local_process",
        "remote_service",
    )
    require_latest_history_entry: bool = field(default=True, init=False)
    require_ready_descriptor: bool = field(default=True, init=False)
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_POLICY_SCHEMA:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "unsupported Scheduler approved revision selection policy schema"
            )
        _require_typed_ref(
            "policy_ref", self.policy_ref, required_prefixes=_POLICY_PREFIXES
        )
        _require_typed_ref(
            "scheduler_ref", self.scheduler_ref, required_prefixes=_SCHEDULER_PREFIXES
        )
        object.__setattr__(
            self,
            "allowed_laboratory_refs",
            _normalize_refs(
                "allowed_laboratory_refs",
                self.allowed_laboratory_refs,
                required_prefixes=_LABORATORY_PREFIXES,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "allowed_visit_modes",
            _normalize_literals(
                "allowed_visit_modes",
                self.allowed_visit_modes,
                allowed=_ALLOWED_VISIT_MODES,
            ),
        )
        object.__setattr__(
            self,
            "allowed_execution_boundaries",
            _normalize_literals(
                "allowed_execution_boundaries",
                self.allowed_execution_boundaries,
                allowed=_ALLOWED_EXECUTION_BOUNDARIES,
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

    def to_mapping(self, *, include_digest: bool = True) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "policy_ref": self.policy_ref,
            "scheduler_ref": self.scheduler_ref,
            "allowed_laboratory_refs": list(self.allowed_laboratory_refs),
            "allowed_visit_modes": list(self.allowed_visit_modes),
            "allowed_execution_boundaries": list(
                self.allowed_execution_boundaries
            ),
            "require_latest_history_entry": self.require_latest_history_entry,
            "require_ready_descriptor": self.require_ready_descriptor,
            "metadata": dict(self.metadata),
            "requires_durable_sql_history": True,
            "requires_operator_approval": True,
            "scheduler_remains_only_orchestrator": True,
            "new_scheduler_created": False,
            "parallel_orchestrator_created": False,
        }
        if include_digest:
            mapping["policy_digest"] = self.policy_digest
        return mapping


@dataclass(frozen=True, slots=True)
class SchedulerApprovedSpecialistRevisionSelectionCommand:
    """Immutable request to select one durable, approved specialist revision."""

    schema: str
    command_ref: str
    selection_ref: str
    scheduler_ref: str
    history_result: SpecialistCapabilityGrowthHistoryAppendResult
    expected_snapshot_digest_sha256: str
    specialist_ref: str
    capability: str
    input_contract_ref: str
    output_contract_ref: str
    laboratory_ref: str
    visit_mode: SpecialistLaboratoryVisitMode
    available_laboratory_capabilities: tuple[str, ...]
    available_execution_boundaries: tuple[SpecialistExecutionBoundary, ...]
    conversation_ref: str
    context_refs: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_COMMAND_SCHEMA:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "unsupported Scheduler approved revision selection command schema"
            )
        _require_typed_ref(
            "command_ref", self.command_ref, required_prefixes=_COMMAND_PREFIXES
        )
        _require_typed_ref(
            "selection_ref", self.selection_ref, required_prefixes=_SELECTION_PREFIXES
        )
        _require_typed_ref(
            "scheduler_ref", self.scheduler_ref, required_prefixes=_SCHEDULER_PREFIXES
        )
        if not isinstance(
            self.history_result, SpecialistCapabilityGrowthHistoryAppendResult
        ):
            raise TypeError(
                "history_result must be SpecialistCapabilityGrowthHistoryAppendResult"
            )
        _require_sha256(
            "expected_snapshot_digest_sha256",
            self.expected_snapshot_digest_sha256,
        )
        _require_typed_ref(
            "specialist_ref",
            self.specialist_ref,
            required_prefixes=_SPECIALIST_PREFIXES,
        )
        _require_capability("capability", self.capability)
        _require_typed_ref(
            "input_contract_ref",
            self.input_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        _require_typed_ref(
            "output_contract_ref",
            self.output_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        _require_typed_ref(
            "laboratory_ref",
            self.laboratory_ref,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        if self.visit_mode not in _ALLOWED_VISIT_MODES:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "unsupported visit_mode"
            )
        object.__setattr__(
            self,
            "available_laboratory_capabilities",
            _normalize_capabilities(
                "available_laboratory_capabilities",
                self.available_laboratory_capabilities,
            ),
        )
        object.__setattr__(
            self,
            "available_execution_boundaries",
            _normalize_literals(
                "available_execution_boundaries",
                self.available_execution_boundaries,
                allowed=_ALLOWED_EXECUTION_BOUNDARIES,
            ),
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
                "context_refs",
                self.context_refs,
                required_prefixes=_CONTEXT_PREFIXES,
            ),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def command_digest(self) -> str:
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
            "command_ref": self.command_ref,
            "selection_ref": self.selection_ref,
            "scheduler_ref": self.scheduler_ref,
            "history_ref": self.history_result.entry.history_ref,
            "history_entry_ref": self.history_result.entry.entry_ref,
            "history_sql_ref": self.history_result.entry.sql_ref,
            "expected_snapshot_digest_sha256": (
                self.expected_snapshot_digest_sha256
            ),
            "specialist_ref": self.specialist_ref,
            "capability": self.capability,
            "input_contract_ref": self.input_contract_ref,
            "output_contract_ref": self.output_contract_ref,
            "laboratory_ref": self.laboratory_ref,
            "visit_mode": self.visit_mode,
            "available_laboratory_capabilities": list(
                self.available_laboratory_capabilities
            ),
            "available_execution_boundaries": list(
                self.available_execution_boundaries
            ),
            "conversation_ref": self.conversation_ref,
            "context_refs": list(self.context_refs),
            "metadata": dict(self.metadata),
            "requires_existing_scheduler": True,
            "laboratory_dispatch_requested": False,
        }
        if include_digest:
            mapping["command_digest"] = self.command_digest
        return mapping


@dataclass(frozen=True, slots=True)
class SchedulerApprovedSpecialistRevisionSelectionResult:
    """Immutable Scheduler selection; not a laboratory dispatch or execution."""

    schema: str
    selection_ref: str
    command_ref: str
    scheduler_ref: str
    policy_ref: str
    policy_digest_sha256: str
    history_ref: str
    history_snapshot_digest_sha256: str
    history_entry_ref: str
    history_entry_digest_sha256: str
    sql_ref: str
    decision_ref: str
    selected_revision: PortableSpecialistRevision
    capability: str
    input_contract_ref: str
    output_contract_ref: str
    laboratory_ref: str
    visit_mode: SpecialistLaboratoryVisitMode
    execution_boundary: SpecialistExecutionBoundary
    conversation_ref: str
    context_refs: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_RESULT_SCHEMA:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "unsupported Scheduler approved revision selection result schema"
            )
        _require_typed_ref(
            "selection_ref", self.selection_ref, required_prefixes=_SELECTION_PREFIXES
        )
        _require_typed_ref(
            "command_ref", self.command_ref, required_prefixes=_COMMAND_PREFIXES
        )
        _require_typed_ref(
            "scheduler_ref", self.scheduler_ref, required_prefixes=_SCHEDULER_PREFIXES
        )
        _require_typed_ref(
            "policy_ref", self.policy_ref, required_prefixes=_POLICY_PREFIXES
        )
        _require_sha256("policy_digest_sha256", self.policy_digest_sha256)
        _require_typed_ref("history_ref", self.history_ref, required_prefixes=("history:",))
        _require_sha256(
            "history_snapshot_digest_sha256",
            self.history_snapshot_digest_sha256,
        )
        _require_typed_ref(
            "history_entry_ref",
            self.history_entry_ref,
            required_prefixes=("history-entry:",),
        )
        _require_sha256(
            "history_entry_digest_sha256",
            self.history_entry_digest_sha256,
        )
        _require_typed_ref("sql_ref", self.sql_ref, required_prefixes=("sql:",))
        _require_typed_ref(
            "decision_ref", self.decision_ref, required_prefixes=("decision:",)
        )
        if not isinstance(self.selected_revision, PortableSpecialistRevision):
            raise TypeError("selected_revision must be PortableSpecialistRevision")
        _require_capability("capability", self.capability)
        _require_typed_ref(
            "input_contract_ref",
            self.input_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        _require_typed_ref(
            "output_contract_ref",
            self.output_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        _require_typed_ref(
            "laboratory_ref",
            self.laboratory_ref,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        if self.visit_mode not in _ALLOWED_VISIT_MODES:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "unsupported visit_mode"
            )
        if self.execution_boundary not in _ALLOWED_EXECUTION_BOUNDARIES:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "unsupported execution_boundary"
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
                "context_refs",
                self.context_refs,
                required_prefixes=_CONTEXT_PREFIXES,
            ),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def specialist_ref(self) -> str:
        return self.selected_revision.specialist_ref

    @property
    def selection_digest(self) -> str:
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
            "selection_ref": self.selection_ref,
            "command_ref": self.command_ref,
            "scheduler_ref": self.scheduler_ref,
            "policy_ref": self.policy_ref,
            "policy_digest_sha256": self.policy_digest_sha256,
            "history_ref": self.history_ref,
            "history_snapshot_digest_sha256": (
                self.history_snapshot_digest_sha256
            ),
            "history_entry_ref": self.history_entry_ref,
            "history_entry_digest_sha256": self.history_entry_digest_sha256,
            "sql_ref": self.sql_ref,
            "decision_ref": self.decision_ref,
            "selected_revision": self.selected_revision.to_mapping(),
            "specialist_ref": self.specialist_ref,
            "capability": self.capability,
            "input_contract_ref": self.input_contract_ref,
            "output_contract_ref": self.output_contract_ref,
            "laboratory_ref": self.laboratory_ref,
            "visit_mode": self.visit_mode,
            "execution_boundary": self.execution_boundary,
            "conversation_ref": self.conversation_ref,
            "context_refs": list(self.context_refs),
            "metadata": dict(self.metadata),
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
        if include_digest:
            mapping["selection_digest"] = self.selection_digest
        return mapping


class SchedulerApprovedSpecialistRevisionSelector:
    """Pure selection use case invoked by the existing Scheduler handler path."""

    def select(
        self,
        command: SchedulerApprovedSpecialistRevisionSelectionCommand,
        policy: SchedulerApprovedSpecialistRevisionSelectionPolicy,
    ) -> SchedulerApprovedSpecialistRevisionSelectionResult:
        if not isinstance(
            command, SchedulerApprovedSpecialistRevisionSelectionCommand
        ):
            raise TypeError(
                "command must be SchedulerApprovedSpecialistRevisionSelectionCommand"
            )
        if not isinstance(
            policy, SchedulerApprovedSpecialistRevisionSelectionPolicy
        ):
            raise TypeError(
                "policy must be SchedulerApprovedSpecialistRevisionSelectionPolicy"
            )
        if command.scheduler_ref != policy.scheduler_ref:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "command scheduler_ref must match selection policy"
            )

        history_result = command.history_result
        if not history_result.durable_write_performed:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "selection requires a durable SQL-authoritative history result"
            )
        if history_result.adapter_kind == "deterministic_test_memory":
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "selection rejects the deterministic test-only history adapter"
            )
        snapshot = history_result.snapshot
        entry = history_result.entry
        if command.expected_snapshot_digest_sha256 != snapshot.snapshot_digest:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "expected history snapshot digest does not match"
            )
        if policy.require_latest_history_entry and (
            entry.entry_ref != snapshot.latest_entry.entry_ref
            or entry.entry_digest != snapshot.latest_entry.entry_digest
        ):
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "selection requires the latest durable history entry"
            )
        if not entry.decision.revision_authorized:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "history entry revision is not operator-approved"
            )
        if command.specialist_ref != entry.specialist_ref:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "command specialist_ref must match durable history"
            )
        revision = entry.revision
        descriptor = revision.descriptor
        if policy.require_ready_descriptor and descriptor.availability != "ready":
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "selected specialist descriptor must be ready"
            )

        capability = _find_capability(descriptor, command.capability)
        if command.input_contract_ref not in descriptor.accepted_input_contract_refs:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "input contract is not accepted by specialist descriptor"
            )
        if command.input_contract_ref not in capability.accepted_input_contract_refs:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "input contract is not accepted by requested capability"
            )
        if command.output_contract_ref not in descriptor.produced_output_contract_refs:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "output contract is not produced by specialist descriptor"
            )
        if command.output_contract_ref not in capability.produced_output_contract_refs:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "output contract is not produced by requested capability"
            )

        binding = next(
            (
                item
                for item in descriptor.laboratory_bindings
                if item.laboratory_ref == command.laboratory_ref
            ),
            None,
        )
        if binding is None:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "laboratory is not declared by selected specialist revision"
            )
        if policy.allowed_laboratory_refs and (
            command.laboratory_ref not in policy.allowed_laboratory_refs
        ):
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "laboratory is not allowed by Scheduler selection policy"
            )
        if command.visit_mode not in policy.allowed_visit_modes:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "visit mode is not allowed by Scheduler selection policy"
            )
        if command.visit_mode not in binding.visit_modes:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "visit mode is not allowed by specialist laboratory binding"
            )
        missing_laboratory_capabilities = set(
            binding.required_laboratory_capabilities
        ).difference(command.available_laboratory_capabilities)
        if missing_laboratory_capabilities:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "target laboratory does not provide required capabilities: "
                + ", ".join(sorted(missing_laboratory_capabilities))
            )
        execution_boundary = _select_execution_boundary(
            descriptor,
            command.available_execution_boundaries,
            policy.allowed_execution_boundaries,
        )
        return SchedulerApprovedSpecialistRevisionSelectionResult(
            schema=SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_RESULT_SCHEMA,
            selection_ref=command.selection_ref,
            command_ref=command.command_ref,
            scheduler_ref=command.scheduler_ref,
            policy_ref=policy.policy_ref,
            policy_digest_sha256=policy.policy_digest,
            history_ref=entry.history_ref,
            history_snapshot_digest_sha256=snapshot.snapshot_digest,
            history_entry_ref=entry.entry_ref,
            history_entry_digest_sha256=entry.entry_digest,
            sql_ref=entry.sql_ref,
            decision_ref=entry.decision.decision_ref,
            selected_revision=revision,
            capability=command.capability,
            input_contract_ref=command.input_contract_ref,
            output_contract_ref=command.output_contract_ref,
            laboratory_ref=command.laboratory_ref,
            visit_mode=command.visit_mode,
            execution_boundary=execution_boundary,
            conversation_ref=command.conversation_ref,
            context_refs=command.context_refs,
            metadata=command.metadata,
        )


class SchedulerApprovedSpecialistRevisionSelectionHandler:
    """Dispatcher-compatible handler for the existing Scheduler event path."""

    def __init__(
        self,
        policy: SchedulerApprovedSpecialistRevisionSelectionPolicy,
        selector: SchedulerApprovedSpecialistRevisionSelector | None = None,
    ) -> None:
        self.policy = policy
        self.selector = selector or SchedulerApprovedSpecialistRevisionSelector()

    async def handle(
        self, event: Event
    ) -> SchedulerApprovedSpecialistRevisionSelectionResult:
        if not isinstance(event, Event):
            raise TypeError("event must be Event")
        if event.type is not EventType.SPECIALIST_REVISION_SELECTION:
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "handler only accepts SPECIALIST_REVISION_SELECTION events"
            )
        if not isinstance(
            event.payload, SchedulerApprovedSpecialistRevisionSelectionCommand
        ):
            raise TypeError(
                "event payload must be SchedulerApprovedSpecialistRevisionSelectionCommand"
            )
        return self.selector.select(event.payload, self.policy)


@runtime_checkable
class SchedulerDispatcherRegistrationPort(Protocol):
    """Minimal composition boundary already implemented by kernel.Dispatcher."""

    def register(self, event_type: EventType, handler: object) -> None:
        """Register one handler on the existing Dispatcher."""


def register_scheduler_approved_specialist_revision_selection(
    dispatcher: SchedulerDispatcherRegistrationPort,
    handler: SchedulerApprovedSpecialistRevisionSelectionHandler,
) -> None:
    """Register r6 on the existing Dispatcher; create no registry or Scheduler."""

    if not isinstance(handler, SchedulerApprovedSpecialistRevisionSelectionHandler):
        raise TypeError(
            "handler must be SchedulerApprovedSpecialistRevisionSelectionHandler"
        )
    dispatcher.register(EventType.SPECIALIST_REVISION_SELECTION, handler)


def build_scheduler_approved_specialist_revision_selection_event(
    command: SchedulerApprovedSpecialistRevisionSelectionCommand,
    *,
    source: str = "specialist-capability-growth",
    priority: int = 0,
    correlation_id: str | None = None,
) -> Event:
    """Build the immutable event consumed through Scheduler.emit()."""

    if not isinstance(command, SchedulerApprovedSpecialistRevisionSelectionCommand):
        raise TypeError(
            "command must be SchedulerApprovedSpecialistRevisionSelectionCommand"
        )
    if not isinstance(source, str) or not source.strip():
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            "event source must be non-empty"
        )
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            "event priority must be an integer"
        )
    return Event(
        type=EventType.SPECIALIST_REVISION_SELECTION,
        source=source.strip(),
        dest="scheduler",
        payload=command,
        priority=priority,
        correlation_id=correlation_id,
        metadata=MappingProxyType(
            {
                "phase": "0285-r6",
                "selection_ref": command.selection_ref,
                "specialist_ref": command.specialist_ref,
            }
        ),
    )


def _find_capability(
    descriptor: PortableSpecialistDescriptor,
    capability_name: str,
) -> SpecialistCapabilityContract:
    capability = next(
        (
            item
            for item in descriptor.capabilities
            if item.capability == capability_name
        ),
        None,
    )
    if capability is None:
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            "requested capability is not declared by selected revision"
        )
    return capability


def _select_execution_boundary(
    descriptor: PortableSpecialistDescriptor,
    available: tuple[SpecialistExecutionBoundary, ...],
    allowed: tuple[SpecialistExecutionBoundary, ...],
) -> SpecialistExecutionBoundary:
    available_set = frozenset(available)
    allowed_set = frozenset(allowed)
    for boundary in descriptor.execution_profile.preferred_execution_boundaries:
        if boundary in available_set and boundary in allowed_set:
            return boundary
    raise SchedulerApprovedSpecialistRevisionSelectionError(
        "no compatible execution boundary is available"
    )


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefixes: tuple[str, ...],
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(required_prefixes):
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_sha256(name: str, value: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            f"{name} must be a lowercase SHA-256 digest"
        )


def _require_capability(name: str, value: str) -> None:
    if not isinstance(value, str) or not _CAPABILITY_RE.fullmatch(value):
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            f"{name} must use lowercase dotted identifier syntax"
        )


def _normalize_refs(
    name: str,
    values: Sequence[str],
    *,
    required_prefixes: tuple[str, ...],
    allow_empty: bool = False,
) -> tuple[str, ...]:
    normalized = tuple(values)
    if not normalized and not allow_empty:
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            f"{name} must not be empty"
        )
    for value in normalized:
        _require_typed_ref(name, value, required_prefixes=required_prefixes)
    return tuple(dict.fromkeys(normalized))


def _normalize_capabilities(
    name: str,
    values: Sequence[str],
) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(values))
    if not normalized:
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            f"{name} must not be empty"
        )
    for value in normalized:
        _require_capability(name, value)
    return normalized


def _normalize_literals(
    name: str,
    values: Sequence[str],
    *,
    allowed: frozenset[str],
) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(values))
    if not normalized:
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            f"{name} must not be empty"
        )
    if any(value not in allowed for value in normalized):
        raise SchedulerApprovedSpecialistRevisionSelectionError(
            f"unsupported value in {name}"
        )
    return normalized


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        if not isinstance(key, str) or not key.strip():
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "metadata key must be non-empty"
            )
        if not isinstance(value, str) or not value.strip():
            raise SchedulerApprovedSpecialistRevisionSelectionError(
                "metadata value must be non-empty"
            )
        normalized[key.strip()] = value.strip()
    return tuple(sorted(normalized.items()))


__all__ = (
    "SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_COMMAND_SCHEMA",
    "SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_CONTRACT_VERSION",
    "SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_POLICY_SCHEMA",
    "SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_RESULT_SCHEMA",
    "SchedulerApprovedSpecialistRevisionSelectionCommand",
    "SchedulerApprovedSpecialistRevisionSelectionError",
    "SchedulerApprovedSpecialistRevisionSelectionHandler",
    "SchedulerApprovedSpecialistRevisionSelectionPolicy",
    "SchedulerApprovedSpecialistRevisionSelectionResult",
    "SchedulerApprovedSpecialistRevisionSelector",
    "SchedulerDispatcherRegistrationPort",
    "build_scheduler_approved_specialist_revision_selection_event",
    "register_scheduler_approved_specialist_revision_selection",
)
