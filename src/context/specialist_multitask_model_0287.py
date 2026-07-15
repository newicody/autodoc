"""Extensible multitask specialist contracts for phase 0287-r7-r8-r1.

The module extends the existing portable specialist descriptor with explicit
versioned task, plan and result contracts.  It does not create a Scheduler,
queue, worker, registry, laboratory runtime, model runtime or transport.

OpenVINO is referenced as an existing execution backend through immutable
bindings.  The module never imports or reimplements OpenVINO.  PyTorch,
Transformers and other development tools may later be exposed by additional
backend bindings without changing the public specialist task contracts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Protocol
import hashlib
import re

from context.portable_specialist_contract_0284 import (
    PortableSpecialistDescriptor,
    SpecialistCapabilityContract,
)
from context.specialist_deep_analysis_contract_0287 import (
    DeepAnalysisContribution,
    DeepAnalysisRequest,
    validate_contribution_for_request,
)
from context.specialist_laboratory_message_v2_0287 import (
    SpecialistArtifactReference,
    SpecialistExchangeError,
)

SPECIALIST_MULTITASK_MODEL_VERSION = "0287.r7.r8.r1"
SPECIALIST_TASK_TYPE_SCHEMA = "missipy.specialist.task_type.v1"
SPECIALIST_TASK_EXECUTION_BINDING_SCHEMA = (
    "missipy.specialist.task_execution_binding.v1"
)
SPECIALIST_TASK_REQUEST_SCHEMA = "missipy.specialist.task_request.v1"
SPECIALIST_TASK_DEPENDENCY_SCHEMA = "missipy.specialist.task_dependency.v1"
SPECIALIST_TASK_PLAN_SCHEMA = "missipy.specialist.task_plan.v1"
SPECIALIST_FOLLOWUP_TASK_PROPOSAL_SCHEMA = (
    "missipy.specialist.followup_task_proposal.v1"
)
SPECIALIST_TASK_RESULT_SCHEMA = "missipy.specialist.task_result.v1"
EXTENSIBLE_MULTITASK_SPECIALIST_SCHEMA = (
    "missipy.specialist.multitask_definition.v1"
)

SpecialistTaskStatus = Literal[
    "completed",
    "partial",
    "needs_context",
    "needs_review",
    "failed",
    "cancelled",
    "timed_out",
]
SpecialistTaskDependencyKind = Literal[
    "requires",
    "after",
    "consumes_artifact_from",
    "reviews",
]

_ALLOWED_TASK_STATUSES = frozenset(
    {
        "completed",
        "partial",
        "needs_context",
        "needs_review",
        "failed",
        "cancelled",
        "timed_out",
    }
)
_ALLOWED_DEPENDENCY_KINDS = frozenset(
    {"requires", "after", "consumes_artifact_from", "reviews"}
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_TASK_TYPE_PREFIXES = ("specialist-task-type:", "task-type:")
_TASK_PREFIXES = ("specialist-task:",)
_TASK_PLAN_PREFIXES = ("specialist-task-plan:",)
_TASK_PROPOSAL_PREFIXES = ("specialist-task-proposal:",)
_MISSION_PREFIXES = ("mission:",)
_CONVERSATION_PREFIXES = ("laboratory-conversation:",)
_ROUTE_PREFIXES = ("route:", "specialist-path:")
_CONTRACT_PREFIXES = ("contract:",)
_CONTEXT_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "qdrant:",
    "artifact:",
    "dataset:",
    "research-work-package:",
)
_EVIDENCE_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "artifact:",
    "dataset:",
    "validation:",
)
_BACKEND_PREFIXES = (
    "openvino:",
    "python:",
    "runtime:",
    "pytorch:",
    "transformers:",
)
_MODEL_PREFIXES = ("model:",)
_TOKENIZER_PREFIXES = ("tokenizer:",)
_RUNTIME_CONTRACT_PREFIXES = ("contract:",)
_DEVICE_PREFIXES = ("device:", "openvino:", "accelerator:")
_PROVENANCE_PREFIXES = (
    "laboratory-visit:",
    "specialist-task:",
    "specialist-task-plan:",
    "validation:",
    "artifact:",
    "sql:",
)
_MAX_ITEMS = 1_024
_MAX_TEXT_CHARS = 1_000_000
_MAX_PRIORITY = 10_000
_MAX_PARALLELISM = 1_024
_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))


class SpecialistMultitaskContractError(ValueError):
    """Raised when one multitask-specialist contract is incoherent."""


@dataclass(frozen=True, slots=True)
class SpecialistTaskType:
    """One extensible task type bound to an existing specialist capability."""

    schema: str
    task_type_ref: str
    capability: str
    description: str
    accepted_input_contract_refs: tuple[str, ...]
    produced_output_contract_refs: tuple[str, ...]
    contribution_kinds: tuple[str, ...] = ()
    supports_batch: bool = False
    supports_resume: bool = False
    supports_review: bool = False
    deterministic: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_TASK_TYPE_SCHEMA:
            raise SpecialistMultitaskContractError(
                "unsupported specialist task type schema"
            )
        _require_typed_ref(
            "task_type_ref",
            self.task_type_ref,
            required_prefixes=_TASK_TYPE_PREFIXES,
        )
        _require_identifier("capability", self.capability)
        _require_text("description", self.description)
        object.__setattr__(
            self,
            "accepted_input_contract_refs",
            _normalize_refs(
                "accepted_input_contract_refs",
                self.accepted_input_contract_refs,
                required_prefixes=_CONTRACT_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "produced_output_contract_refs",
            _normalize_refs(
                "produced_output_contract_refs",
                self.produced_output_contract_refs,
                required_prefixes=_CONTRACT_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "contribution_kinds",
            _normalize_identifiers(
                "contribution_kinds",
                self.contribution_kinds,
                allow_empty=True,
            ),
        )
        for name in (
            "supports_batch",
            "supports_resume",
            "supports_review",
            "deterministic",
        ):
            _require_bool(name, getattr(self, name))
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "task_type_ref": self.task_type_ref,
            "capability": self.capability,
            "description": self.description,
            "accepted_input_contract_refs": list(
                self.accepted_input_contract_refs
            ),
            "produced_output_contract_refs": list(
                self.produced_output_contract_refs
            ),
            "contribution_kinds": list(self.contribution_kinds),
            "supports_batch": self.supports_batch,
            "supports_resume": self.supports_resume,
            "supports_review": self.supports_review,
            "deterministic": self.deterministic,
            "metadata": _thaw_json(self.metadata),
            "scheduler_task_created": False,
            "handler_attached": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistTaskExecutionBinding:
    """Portable reference to an existing execution backend and model bundle."""

    schema: str
    backend_ref: str
    operation: str
    runtime_contract_ref: str
    model_ref: str | None = None
    tokenizer_ref: str | None = None
    model_sha256: str | None = None
    device_refs: tuple[str, ...] = ()
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_TASK_EXECUTION_BINDING_SCHEMA:
            raise SpecialistMultitaskContractError(
                "unsupported specialist task execution binding schema"
            )
        _require_typed_ref(
            "backend_ref",
            self.backend_ref,
            required_prefixes=_BACKEND_PREFIXES,
        )
        _require_identifier("operation", self.operation)
        _require_typed_ref(
            "runtime_contract_ref",
            self.runtime_contract_ref,
            required_prefixes=_RUNTIME_CONTRACT_PREFIXES,
        )
        if self.model_ref is not None:
            _require_typed_ref(
                "model_ref",
                self.model_ref,
                required_prefixes=_MODEL_PREFIXES,
            )
        if self.tokenizer_ref is not None:
            _require_typed_ref(
                "tokenizer_ref",
                self.tokenizer_ref,
                required_prefixes=_TOKENIZER_PREFIXES,
            )
        if self.tokenizer_ref is not None and self.model_ref is None:
            raise SpecialistMultitaskContractError(
                "tokenizer_ref requires model_ref"
            )
        if self.model_sha256 is not None:
            if self.model_ref is None:
                raise SpecialistMultitaskContractError(
                    "model_sha256 requires model_ref"
                )
            _require_sha256("model_sha256", self.model_sha256)
        object.__setattr__(
            self,
            "device_refs",
            _normalize_refs(
                "device_refs",
                self.device_refs,
                allow_empty=True,
                required_prefixes=_DEVICE_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "parameters",
            _freeze_json_mapping(self.parameters),
        )

    @property
    def reuses_existing_openvino_backend(self) -> bool:
        return self.backend_ref.startswith("openvino:")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "backend_ref": self.backend_ref,
            "operation": self.operation,
            "runtime_contract_ref": self.runtime_contract_ref,
            "model_ref": self.model_ref,
            "tokenizer_ref": self.tokenizer_ref,
            "model_sha256": self.model_sha256,
            "device_refs": list(self.device_refs),
            "parameters": _thaw_json(self.parameters),
            "reuses_existing_openvino_backend": (
                self.reuses_existing_openvino_backend
            ),
            "backend_implementation_created": False,
            "openvino_reimplemented": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistTaskRequest:
    """One immutable invocation of one explicit specialist capability."""

    schema: str
    task_ref: str
    plan_ref: str
    mission_ref: str
    specialist_ref: str
    task_type_ref: str
    capability: str
    objective: str
    input_contract_ref: str
    expected_output_contract_ref: str
    conversation_ref: str
    return_route_ref: str
    constraints: tuple[str, ...]
    success_criteria: tuple[str, ...]
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    input_artifact_refs: tuple[SpecialistArtifactReference, ...] = ()
    priority: int = 100
    idempotency_key: str = ""
    execution_binding: SpecialistTaskExecutionBinding | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_TASK_REQUEST_SCHEMA:
            raise SpecialistMultitaskContractError(
                "unsupported specialist task request schema"
            )
        _require_typed_ref(
            "task_ref", self.task_ref, required_prefixes=_TASK_PREFIXES
        )
        _require_typed_ref(
            "plan_ref", self.plan_ref, required_prefixes=_TASK_PLAN_PREFIXES
        )
        _require_typed_ref(
            "mission_ref", self.mission_ref, required_prefixes=_MISSION_PREFIXES
        )
        _require_typed_ref(
            "specialist_ref",
            self.specialist_ref,
            required_prefixes=_SPECIALIST_PREFIXES,
        )
        _require_typed_ref(
            "task_type_ref",
            self.task_type_ref,
            required_prefixes=_TASK_TYPE_PREFIXES,
        )
        _require_identifier("capability", self.capability)
        _require_text("objective", self.objective)
        _require_typed_ref(
            "input_contract_ref",
            self.input_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        _require_typed_ref(
            "expected_output_contract_ref",
            self.expected_output_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        _require_typed_ref(
            "conversation_ref",
            self.conversation_ref,
            required_prefixes=_CONVERSATION_PREFIXES,
        )
        _require_typed_ref(
            "return_route_ref",
            self.return_route_ref,
            required_prefixes=_ROUTE_PREFIXES,
        )
        object.__setattr__(
            self,
            "constraints",
            _normalize_texts("constraints", self.constraints, allow_empty=True),
        )
        object.__setattr__(
            self,
            "success_criteria",
            _normalize_texts(
                "success_criteria",
                self.success_criteria,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs(
                "context_refs",
                self.context_refs,
                allow_empty=True,
                required_prefixes=_CONTEXT_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs",
                self.evidence_refs,
                allow_empty=True,
                required_prefixes=_EVIDENCE_PREFIXES,
            ),
        )
        artifacts = tuple(self.input_artifact_refs)
        if not all(
            isinstance(item, SpecialistArtifactReference) for item in artifacts
        ):
            raise SpecialistMultitaskContractError(
                "input_artifact_refs must contain SpecialistArtifactReference values"
            )
        artifact_refs = tuple(item.artifact_ref for item in artifacts)
        if len(set(artifact_refs)) != len(artifact_refs):
            raise SpecialistMultitaskContractError(
                "input_artifact_refs must contain unique artifact_ref values"
            )
        object.__setattr__(self, "input_artifact_refs", artifacts)
        _require_int_range(
            "priority", self.priority, minimum=0, maximum=_MAX_PRIORITY
        )
        _require_text("idempotency_key", self.idempotency_key)
        if self.execution_binding is not None and not isinstance(
            self.execution_binding,
            SpecialistTaskExecutionBinding,
        ):
            raise SpecialistMultitaskContractError(
                "execution_binding must be SpecialistTaskExecutionBinding"
            )
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "task_ref": self.task_ref,
            "plan_ref": self.plan_ref,
            "mission_ref": self.mission_ref,
            "specialist_ref": self.specialist_ref,
            "task_type_ref": self.task_type_ref,
            "capability": self.capability,
            "objective": self.objective,
            "input_contract_ref": self.input_contract_ref,
            "expected_output_contract_ref": self.expected_output_contract_ref,
            "conversation_ref": self.conversation_ref,
            "return_route_ref": self.return_route_ref,
            "constraints": list(self.constraints),
            "success_criteria": list(self.success_criteria),
            "context_refs": list(self.context_refs),
            "evidence_refs": list(self.evidence_refs),
            "input_artifact_refs": [
                item.to_mapping() for item in self.input_artifact_refs
            ],
            "priority": self.priority,
            "idempotency_key": self.idempotency_key,
            "execution_binding": (
                self.execution_binding.to_mapping()
                if self.execution_binding is not None
                else None
            ),
            "metadata": _thaw_json(self.metadata),
            "scheduler_submission_required": True,
            "scheduler_decision_embedded": False,
            "specialist_can_launch_followups": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistTaskDependency:
    """One edge in a Scheduler-owned specialist task dependency graph."""

    schema: str
    task_ref: str
    depends_on_task_ref: str
    kind: SpecialistTaskDependencyKind

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_TASK_DEPENDENCY_SCHEMA:
            raise SpecialistMultitaskContractError(
                "unsupported specialist task dependency schema"
            )
        _require_typed_ref(
            "task_ref", self.task_ref, required_prefixes=_TASK_PREFIXES
        )
        _require_typed_ref(
            "depends_on_task_ref",
            self.depends_on_task_ref,
            required_prefixes=_TASK_PREFIXES,
        )
        if self.task_ref == self.depends_on_task_ref:
            raise SpecialistMultitaskContractError(
                "task dependency cannot reference itself"
            )
        if self.kind not in _ALLOWED_DEPENDENCY_KINDS:
            raise SpecialistMultitaskContractError(
                "unsupported specialist task dependency kind"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "task_ref": self.task_ref,
            "depends_on_task_ref": self.depends_on_task_ref,
            "kind": self.kind,
        }


@dataclass(frozen=True, slots=True)
class SpecialistTaskPlan:
    """Immutable multitask plan whose execution remains owned by Scheduler."""

    schema: str
    plan_ref: str
    mission_ref: str
    specialist_ref: str
    tasks: tuple[SpecialistTaskRequest, ...]
    dependencies: tuple[SpecialistTaskDependency, ...] = ()
    requested_parallelism: int = 1

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_TASK_PLAN_SCHEMA:
            raise SpecialistMultitaskContractError(
                "unsupported specialist task plan schema"
            )
        _require_typed_ref(
            "plan_ref", self.plan_ref, required_prefixes=_TASK_PLAN_PREFIXES
        )
        _require_typed_ref(
            "mission_ref", self.mission_ref, required_prefixes=_MISSION_PREFIXES
        )
        _require_typed_ref(
            "specialist_ref",
            self.specialist_ref,
            required_prefixes=_SPECIALIST_PREFIXES,
        )
        tasks = tuple(self.tasks)
        if not tasks or not all(
            isinstance(item, SpecialistTaskRequest) for item in tasks
        ):
            raise SpecialistMultitaskContractError(
                "tasks must contain SpecialistTaskRequest values"
            )
        task_refs = tuple(item.task_ref for item in tasks)
        if len(set(task_refs)) != len(task_refs):
            raise SpecialistMultitaskContractError(
                "task plan task_ref values must be unique"
            )
        idempotency_keys = tuple(item.idempotency_key for item in tasks)
        if len(set(idempotency_keys)) != len(idempotency_keys):
            raise SpecialistMultitaskContractError(
                "task plan idempotency keys must be unique"
            )
        for task in tasks:
            if task.plan_ref != self.plan_ref:
                raise SpecialistMultitaskContractError(
                    "task plan_ref must match containing plan"
                )
            if task.mission_ref != self.mission_ref:
                raise SpecialistMultitaskContractError(
                    "task mission_ref must match containing plan"
                )
            if task.specialist_ref != self.specialist_ref:
                raise SpecialistMultitaskContractError(
                    "task specialist_ref must match containing plan"
                )
        object.__setattr__(self, "tasks", tasks)
        dependencies = tuple(self.dependencies)
        if not all(
            isinstance(item, SpecialistTaskDependency) for item in dependencies
        ):
            raise SpecialistMultitaskContractError(
                "dependencies must contain SpecialistTaskDependency values"
            )
        task_ref_set = frozenset(task_refs)
        dependency_keys: set[tuple[str, str, str]] = set()
        for dependency in dependencies:
            if dependency.task_ref not in task_ref_set:
                raise SpecialistMultitaskContractError(
                    "dependency task_ref is not present in plan"
                )
            if dependency.depends_on_task_ref not in task_ref_set:
                raise SpecialistMultitaskContractError(
                    "dependency depends_on_task_ref is not present in plan"
                )
            key = (
                dependency.task_ref,
                dependency.depends_on_task_ref,
                dependency.kind,
            )
            if key in dependency_keys:
                raise SpecialistMultitaskContractError(
                    "duplicate task dependency"
                )
            dependency_keys.add(key)
        _assert_acyclic(task_refs, dependencies)
        object.__setattr__(self, "dependencies", dependencies)
        _require_int_range(
            "requested_parallelism",
            self.requested_parallelism,
            minimum=1,
            maximum=min(_MAX_PARALLELISM, len(tasks)),
        )

    def ready_task_refs(
        self,
        completed_task_refs: Sequence[str] = (),
    ) -> tuple[str, ...]:
        """Return dependency-ready refs without scheduling or executing them."""

        completed = frozenset(completed_task_refs)
        known = frozenset(task.task_ref for task in self.tasks)
        if not completed.issubset(known):
            raise SpecialistMultitaskContractError(
                "completed_task_refs contains a task outside the plan"
            )
        dependencies_by_task: dict[str, set[str]] = {
            task.task_ref: set() for task in self.tasks
        }
        for dependency in self.dependencies:
            dependencies_by_task[dependency.task_ref].add(
                dependency.depends_on_task_ref
            )
        return tuple(
            task.task_ref
            for task in self.tasks
            if task.task_ref not in completed
            and dependencies_by_task[task.task_ref].issubset(completed)
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_ref": self.plan_ref,
            "mission_ref": self.mission_ref,
            "specialist_ref": self.specialist_ref,
            "tasks": [item.to_mapping() for item in self.tasks],
            "dependencies": [item.to_mapping() for item in self.dependencies],
            "requested_parallelism": self.requested_parallelism,
            "initial_ready_task_refs": list(self.ready_task_refs()),
            "scheduler_owned": True,
            "scheduler_execution_started": False,
            "specialist_self_scheduling": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistFollowupTaskProposal:
    """A specialist proposal that Scheduler may convert into a later task."""

    schema: str
    proposal_ref: str
    source_task_ref: str
    task_type_ref: str
    capability: str
    objective: str
    expected_output_contract_ref: str
    reason: str
    requested_specialist_ref: str | None = None
    required_context_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_FOLLOWUP_TASK_PROPOSAL_SCHEMA:
            raise SpecialistMultitaskContractError(
                "unsupported followup task proposal schema"
            )
        _require_typed_ref(
            "proposal_ref",
            self.proposal_ref,
            required_prefixes=_TASK_PROPOSAL_PREFIXES,
        )
        _require_typed_ref(
            "source_task_ref",
            self.source_task_ref,
            required_prefixes=_TASK_PREFIXES,
        )
        _require_typed_ref(
            "task_type_ref",
            self.task_type_ref,
            required_prefixes=_TASK_TYPE_PREFIXES,
        )
        _require_identifier("capability", self.capability)
        _require_text("objective", self.objective)
        _require_typed_ref(
            "expected_output_contract_ref",
            self.expected_output_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        _require_text("reason", self.reason)
        if self.requested_specialist_ref is not None:
            _require_typed_ref(
                "requested_specialist_ref",
                self.requested_specialist_ref,
                required_prefixes=_SPECIALIST_PREFIXES,
            )
        object.__setattr__(
            self,
            "required_context_refs",
            _normalize_refs(
                "required_context_refs",
                self.required_context_refs,
                allow_empty=True,
                required_prefixes=_CONTEXT_PREFIXES,
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "proposal_ref": self.proposal_ref,
            "source_task_ref": self.source_task_ref,
            "task_type_ref": self.task_type_ref,
            "capability": self.capability,
            "objective": self.objective,
            "expected_output_contract_ref": self.expected_output_contract_ref,
            "reason": self.reason,
            "requested_specialist_ref": self.requested_specialist_ref,
            "required_context_refs": list(self.required_context_refs),
            "scheduler_approval_required": True,
            "task_created": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistTaskResult:
    """Standard result envelope for any specialist task type."""

    schema: str
    task_ref: str
    plan_ref: str
    specialist_ref: str
    task_type_ref: str
    capability: str
    status: SpecialistTaskStatus
    output_contract_ref: str
    human_representation: str
    machine_payload: Mapping[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()
    artifact_refs: tuple[SpecialistArtifactReference, ...] = ()
    followup_proposals: tuple[SpecialistFollowupTaskProposal, ...] = ()
    requested_specialist_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    error: SpecialistExchangeError | None = None

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_TASK_RESULT_SCHEMA:
            raise SpecialistMultitaskContractError(
                "unsupported specialist task result schema"
            )
        _require_typed_ref(
            "task_ref", self.task_ref, required_prefixes=_TASK_PREFIXES
        )
        _require_typed_ref(
            "plan_ref", self.plan_ref, required_prefixes=_TASK_PLAN_PREFIXES
        )
        _require_typed_ref(
            "specialist_ref",
            self.specialist_ref,
            required_prefixes=_SPECIALIST_PREFIXES,
        )
        _require_typed_ref(
            "task_type_ref",
            self.task_type_ref,
            required_prefixes=_TASK_TYPE_PREFIXES,
        )
        _require_identifier("capability", self.capability)
        if self.status not in _ALLOWED_TASK_STATUSES:
            raise SpecialistMultitaskContractError(
                "unsupported specialist task result status"
            )
        _require_typed_ref(
            "output_contract_ref",
            self.output_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        _require_text("human_representation", self.human_representation)
        object.__setattr__(
            self,
            "machine_payload",
            _freeze_json_mapping(self.machine_payload),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs",
                self.evidence_refs,
                allow_empty=True,
                required_prefixes=_EVIDENCE_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs(
                "context_refs",
                self.context_refs,
                allow_empty=True,
                required_prefixes=_CONTEXT_PREFIXES,
            ),
        )
        artifacts = tuple(self.artifact_refs)
        if not all(
            isinstance(item, SpecialistArtifactReference) for item in artifacts
        ):
            raise SpecialistMultitaskContractError(
                "artifact_refs must contain SpecialistArtifactReference values"
            )
        object.__setattr__(self, "artifact_refs", artifacts)
        proposals = tuple(self.followup_proposals)
        if not all(
            isinstance(item, SpecialistFollowupTaskProposal)
            for item in proposals
        ):
            raise SpecialistMultitaskContractError(
                "followup_proposals must contain SpecialistFollowupTaskProposal values"
            )
        for proposal in proposals:
            if proposal.source_task_ref != self.task_ref:
                raise SpecialistMultitaskContractError(
                    "followup proposal source_task_ref must match result task_ref"
                )
        object.__setattr__(self, "followup_proposals", proposals)
        object.__setattr__(
            self,
            "requested_specialist_refs",
            _normalize_refs(
                "requested_specialist_refs",
                self.requested_specialist_refs,
                allow_empty=True,
                required_prefixes=_SPECIALIST_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "provenance_refs",
            _normalize_refs(
                "provenance_refs",
                self.provenance_refs,
                allow_empty=True,
                required_prefixes=_PROVENANCE_PREFIXES,
            ),
        )
        if self.error is not None and not isinstance(
            self.error,
            SpecialistExchangeError,
        ):
            raise SpecialistMultitaskContractError(
                "error must be SpecialistExchangeError"
            )
        terminal_error_statuses = {"failed", "timed_out"}
        if self.status in terminal_error_statuses and self.error is None:
            raise SpecialistMultitaskContractError(
                "failed and timed_out results require an error"
            )
        if self.status not in terminal_error_statuses and self.error is not None:
            raise SpecialistMultitaskContractError(
                "only failed and timed_out results may contain an error"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "task_ref": self.task_ref,
            "plan_ref": self.plan_ref,
            "specialist_ref": self.specialist_ref,
            "task_type_ref": self.task_type_ref,
            "capability": self.capability,
            "status": self.status,
            "output_contract_ref": self.output_contract_ref,
            "human_representation": self.human_representation,
            "machine_payload": _thaw_json(self.machine_payload),
            "evidence_refs": list(self.evidence_refs),
            "context_refs": list(self.context_refs),
            "artifact_refs": [item.to_mapping() for item in self.artifact_refs],
            "followup_proposals": [
                item.to_mapping() for item in self.followup_proposals
            ],
            "requested_specialist_refs": list(
                self.requested_specialist_refs
            ),
            "provenance_refs": list(self.provenance_refs),
            "error": self.error.to_mapping() if self.error is not None else None,
            "followups_executed": False,
            "scheduler_command_emitted": False,
            "durable_write_performed": False,
        }


@dataclass(frozen=True, slots=True)
class ExtensibleMultitaskSpecialistDefinition:
    """Portable specialist descriptor plus its immutable task-type catalog."""

    schema: str
    descriptor: PortableSpecialistDescriptor
    task_types: tuple[SpecialistTaskType, ...]

    def __post_init__(self) -> None:
        if self.schema != EXTENSIBLE_MULTITASK_SPECIALIST_SCHEMA:
            raise SpecialistMultitaskContractError(
                "unsupported extensible multitask specialist schema"
            )
        if not isinstance(self.descriptor, PortableSpecialistDescriptor):
            raise SpecialistMultitaskContractError(
                "descriptor must be PortableSpecialistDescriptor"
            )
        task_types = tuple(self.task_types)
        if not task_types or not all(
            isinstance(item, SpecialistTaskType) for item in task_types
        ):
            raise SpecialistMultitaskContractError(
                "task_types must contain SpecialistTaskType values"
            )
        task_type_refs = tuple(item.task_type_ref for item in task_types)
        if len(set(task_type_refs)) != len(task_type_refs):
            raise SpecialistMultitaskContractError(
                "task_type_ref values must be unique"
            )
        capabilities = {
            item.capability: item for item in self.descriptor.capabilities
        }
        for task_type in task_types:
            capability = capabilities.get(task_type.capability)
            if capability is None:
                raise SpecialistMultitaskContractError(
                    "task type capability is not declared by specialist"
                )
            _validate_task_type_against_capability(task_type, capability)
        object.__setattr__(self, "task_types", task_types)

    def task_type(self, task_type_ref: str) -> SpecialistTaskType:
        for task_type in self.task_types:
            if task_type.task_type_ref == task_type_ref:
                return task_type
        raise SpecialistMultitaskContractError(
            "task_type_ref is not declared by specialist"
        )

    def validate_request(
        self,
        request: SpecialistTaskRequest,
    ) -> tuple[str, ...]:
        issues: list[str] = []
        if request.specialist_ref != self.descriptor.specialist_ref:
            issues.append("request specialist_ref does not match descriptor")
        try:
            task_type = self.task_type(request.task_type_ref)
        except SpecialistMultitaskContractError:
            issues.append("request task_type_ref is not declared")
            return tuple(issues)
        if request.capability != task_type.capability:
            issues.append("request capability does not match task type")
        if request.input_contract_ref not in task_type.accepted_input_contract_refs:
            issues.append("request input contract is not accepted by task type")
        if (
            request.expected_output_contract_ref
            not in task_type.produced_output_contract_refs
        ):
            issues.append("request output contract is not produced by task type")
        return tuple(issues)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "descriptor": self.descriptor.to_mapping(),
            "task_types": [item.to_mapping() for item in self.task_types],
            "multitask": True,
            "extensible_by_versioned_task_types": True,
            "global_registry_created": False,
            "runtime_attached": False,
            "scheduler_remains_orchestrator": True,
        }


class SpecialistTaskHandler(Protocol):
    """Runtime extension point; implementations live outside this module."""

    task_type_ref: str

    def execute(self, request: SpecialistTaskRequest) -> SpecialistTaskResult:
        """Execute one already-authorized task."""


def build_stable_task_ref(*parts: str) -> str:
    """Build a deterministic task reference from stable public identities."""

    for part in parts:
        _require_text("task ref seed", part)
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"specialist-task:{digest}"


def build_stable_task_plan_ref(*parts: str) -> str:
    """Build a deterministic plan reference without creating a Scheduler plan."""

    for part in parts:
        _require_text("task plan seed", part)
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"specialist-task-plan:{digest}"


def build_stable_task_idempotency_key(*parts: str) -> str:
    """Build a deterministic replay identity for one task request."""

    for part in parts:
        _require_text("task idempotency seed", part)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def deep_analysis_task_type(
    *,
    output_contract_ref: str,
) -> SpecialistTaskType:
    """Expose the existing deep-analysis contract as one generic task type."""

    _require_typed_ref(
        "output_contract_ref",
        output_contract_ref,
        required_prefixes=_CONTRACT_PREFIXES,
    )
    return SpecialistTaskType(
        schema=SPECIALIST_TASK_TYPE_SCHEMA,
        task_type_ref="specialist-task-type:analysis.deep",
        capability="analysis.deep",
        description=(
            "Produce one evidence-linked domain analysis while preserving "
            "detail for later liaison synthesis"
        ),
        accepted_input_contract_refs=(
            "contract:missipy.specialist.deep_analysis_request.v1",
        ),
        produced_output_contract_refs=(output_contract_ref,),
        contribution_kinds=(
            "domain_analysis",
            "local_synthesis",
            "critique",
            "validation",
            "comparison",
            "recommendation",
            "global_synthesis",
        ),
        supports_batch=False,
        supports_resume=True,
        supports_review=True,
        deterministic=False,
        metadata={"existing_contract_reused": True},
    )


def project_deep_analysis_request_to_task(
    request: DeepAnalysisRequest,
    *,
    plan_ref: str,
    task_ref: str | None = None,
    priority: int = 100,
    execution_binding: SpecialistTaskExecutionBinding | None = None,
) -> SpecialistTaskRequest:
    """Wrap the existing deep-analysis request in the generic task envelope."""

    resolved_task_ref = task_ref or build_stable_task_ref(
        request.request_ref,
        plan_ref,
        request.specialist_ref,
        request.requested_contribution_kind,
    )
    return SpecialistTaskRequest(
        schema=SPECIALIST_TASK_REQUEST_SCHEMA,
        task_ref=resolved_task_ref,
        plan_ref=plan_ref,
        mission_ref=request.mission_ref,
        specialist_ref=request.specialist_ref,
        task_type_ref="specialist-task-type:analysis.deep",
        capability="analysis.deep",
        objective=request.objective,
        input_contract_ref=(
            "contract:missipy.specialist.deep_analysis_request.v1"
        ),
        expected_output_contract_ref=request.expected_output_contract_ref,
        conversation_ref=request.conversation_ref,
        return_route_ref=request.return_route_ref,
        constraints=request.constraints,
        success_criteria=request.success_criteria,
        context_refs=request.context_refs,
        evidence_refs=request.evidence_refs,
        input_artifact_refs=(),
        priority=priority,
        idempotency_key=build_stable_task_idempotency_key(
            resolved_task_ref,
            request.request_ref,
            request.work_package_ref,
        ),
        execution_binding=execution_binding,
        metadata={
            "deep_analysis_request_ref": request.request_ref,
            "work_package_ref": request.work_package_ref,
            "requested_contribution_kind": (
                request.requested_contribution_kind
            ),
            "analysis_depth": request.depth,
        },
    )


def project_deep_analysis_contribution_to_task_result(
    request: DeepAnalysisRequest,
    contribution: DeepAnalysisContribution,
    *,
    task: SpecialistTaskRequest,
    followup_proposals: Sequence[SpecialistFollowupTaskProposal] = (),
) -> SpecialistTaskResult:
    """Preserve a deep contribution inside the generic task-result envelope."""

    issues = validate_contribution_for_request(request, contribution)
    if issues:
        raise SpecialistMultitaskContractError("; ".join(issues))
    if task.specialist_ref != request.specialist_ref:
        raise SpecialistMultitaskContractError(
            "task specialist_ref does not match deep-analysis request"
        )
    if task.expected_output_contract_ref != contribution.output_contract_ref:
        raise SpecialistMultitaskContractError(
            "task output contract does not match deep-analysis contribution"
        )
    return SpecialistTaskResult(
        schema=SPECIALIST_TASK_RESULT_SCHEMA,
        task_ref=task.task_ref,
        plan_ref=task.plan_ref,
        specialist_ref=contribution.specialist_ref,
        task_type_ref=task.task_type_ref,
        capability=task.capability,
        status="completed",
        output_contract_ref=contribution.output_contract_ref,
        human_representation=contribution.human_representation,
        machine_payload=contribution.to_mapping(),
        evidence_refs=contribution.evidence_refs,
        context_refs=contribution.requested_context_refs,
        artifact_refs=contribution.artifact_refs,
        followup_proposals=tuple(followup_proposals),
        requested_specialist_refs=contribution.requested_specialist_refs,
        provenance_refs=(task.task_ref, contribution.visit_ref),
    )


def _validate_task_type_against_capability(
    task_type: SpecialistTaskType,
    capability: SpecialistCapabilityContract,
) -> None:
    if not set(task_type.accepted_input_contract_refs).issubset(
        capability.accepted_input_contract_refs
    ):
        raise SpecialistMultitaskContractError(
            "task type input contracts must be accepted by capability"
        )
    if not set(task_type.produced_output_contract_refs).issubset(
        capability.produced_output_contract_refs
    ):
        raise SpecialistMultitaskContractError(
            "task type output contracts must be produced by capability"
        )


def _assert_acyclic(
    task_refs: Sequence[str],
    dependencies: Sequence[SpecialistTaskDependency],
) -> None:
    incoming: dict[str, set[str]] = {task_ref: set() for task_ref in task_refs}
    outgoing: dict[str, set[str]] = {task_ref: set() for task_ref in task_refs}
    for dependency in dependencies:
        incoming[dependency.task_ref].add(dependency.depends_on_task_ref)
        outgoing[dependency.depends_on_task_ref].add(dependency.task_ref)
    ready = [task_ref for task_ref, values in incoming.items() if not values]
    visited = 0
    while ready:
        current = ready.pop()
        visited += 1
        for dependent in tuple(outgoing[current]):
            incoming[dependent].discard(current)
            if not incoming[dependent]:
                ready.append(dependent)
    if visited != len(task_refs):
        raise SpecialistMultitaskContractError(
            "specialist task plan dependencies must be acyclic"
        )


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SpecialistMultitaskContractError(f"{name} must be non-empty")
    if len(value) > _MAX_TEXT_CHARS:
        raise SpecialistMultitaskContractError(
            f"{name} exceeds {_MAX_TEXT_CHARS} characters"
        )


def _require_bool(name: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise SpecialistMultitaskContractError(f"{name} must be a boolean")


def _require_identifier(name: str, value: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise SpecialistMultitaskContractError(
            f"{name} must use lowercase dotted identifier syntax"
        )


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefixes: tuple[str, ...],
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise SpecialistMultitaskContractError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(required_prefixes):
        raise SpecialistMultitaskContractError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_sha256(name: str, value: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise SpecialistMultitaskContractError(
            f"{name} must be a lowercase SHA-256 digest"
        )


def _require_int_range(
    name: str,
    value: int,
    *,
    minimum: int,
    maximum: int,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SpecialistMultitaskContractError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise SpecialistMultitaskContractError(
            f"{name} must be between {minimum} and {maximum}"
        )


def _normalize_texts(
    name: str,
    values: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise SpecialistMultitaskContractError(
            f"{name} must be a sequence of texts"
        )
    normalized: list[str] = []
    for value in values:
        _require_text(name, value)
        normalized.append(value.strip())
    result = tuple(dict.fromkeys(normalized))
    if not result and not allow_empty:
        raise SpecialistMultitaskContractError(f"{name} must not be empty")
    if len(result) > _MAX_ITEMS:
        raise SpecialistMultitaskContractError(
            f"{name} exceeds {_MAX_ITEMS} values"
        )
    return result


def _normalize_identifiers(
    name: str,
    values: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise SpecialistMultitaskContractError(
            f"{name} must be a sequence of identifiers"
        )
    normalized = tuple(dict.fromkeys(values))
    if not normalized and not allow_empty:
        raise SpecialistMultitaskContractError(f"{name} must not be empty")
    if len(normalized) > _MAX_ITEMS:
        raise SpecialistMultitaskContractError(
            f"{name} exceeds {_MAX_ITEMS} values"
        )
    for value in normalized:
        _require_identifier(name, value)
    return normalized


def _normalize_refs(
    name: str,
    refs: Sequence[str],
    *,
    allow_empty: bool = False,
    required_prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(refs, (str, bytes)):
        raise SpecialistMultitaskContractError(
            f"{name} must be a sequence of references"
        )
    values = tuple(dict.fromkeys(refs))
    if not values and not allow_empty:
        raise SpecialistMultitaskContractError(f"{name} must not be empty")
    if len(values) > _MAX_ITEMS:
        raise SpecialistMultitaskContractError(
            f"{name} exceeds {_MAX_ITEMS} values"
        )
    for value in values:
        _require_typed_ref(
            name,
            value,
            required_prefixes=required_prefixes,
        )
    return values


def _freeze_json_mapping(values: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(values, Mapping):
        raise SpecialistMultitaskContractError("value must be a mapping")
    frozen: dict[str, Any] = {}
    for key, value in values.items():
        _require_text("mapping key", key)
        frozen[key] = _freeze_json(value)
    return MappingProxyType(frozen)


def _freeze_json(value: Any) -> Any:
    if isinstance(value, _JSON_SCALAR_TYPES):
        return value
    if isinstance(value, Mapping):
        return _freeze_json_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    raise SpecialistMultitaskContractError(
        f"mapping contains non-JSON value: {type(value).__name__}"
    )


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


__all__ = (
    "EXTENSIBLE_MULTITASK_SPECIALIST_SCHEMA",
    "SPECIALIST_FOLLOWUP_TASK_PROPOSAL_SCHEMA",
    "SPECIALIST_MULTITASK_MODEL_VERSION",
    "SPECIALIST_TASK_DEPENDENCY_SCHEMA",
    "SPECIALIST_TASK_EXECUTION_BINDING_SCHEMA",
    "SPECIALIST_TASK_PLAN_SCHEMA",
    "SPECIALIST_TASK_REQUEST_SCHEMA",
    "SPECIALIST_TASK_RESULT_SCHEMA",
    "SPECIALIST_TASK_TYPE_SCHEMA",
    "ExtensibleMultitaskSpecialistDefinition",
    "SpecialistFollowupTaskProposal",
    "SpecialistMultitaskContractError",
    "SpecialistTaskDependency",
    "SpecialistTaskDependencyKind",
    "SpecialistTaskExecutionBinding",
    "SpecialistTaskHandler",
    "SpecialistTaskPlan",
    "SpecialistTaskRequest",
    "SpecialistTaskResult",
    "SpecialistTaskStatus",
    "SpecialistTaskType",
    "build_stable_task_idempotency_key",
    "build_stable_task_plan_ref",
    "build_stable_task_ref",
    "deep_analysis_task_type",
    "project_deep_analysis_contribution_to_task_result",
    "project_deep_analysis_request_to_task",
)
