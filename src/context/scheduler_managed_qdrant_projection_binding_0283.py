"""Controlled Scheduler-owned real Qdrant projection binding. 0283-r4.

The binding reuses:

* the existing 0262 embedding-to-Qdrant projection use case;
* the existing 0283-r3 scoped executor factory;
* the existing SQL-authority scope and qdrant-client executor underneath r3.

Preview never constructs a client. Execute constructs the scoped binding,
injects it into 0262, performs at most the requested projection and closes the
binding. The module does not modify Scheduler.run and adds no Scheduler,
transport, ControlProxy, EventBus, SHM or MMIO path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from context.scheduler_managed_embedding_qdrant_projection_usage_0262 import (
    SchedulerManagedEmbeddingQdrantProjectionRequest,
    SchedulerManagedEmbeddingQdrantProjectionResult,
    run_scheduler_managed_embedding_qdrant_projection_usage,
)
from inference.qdrant_projection_adapter import QdrantProjectionPolicy
from inference.qdrant_real_binding_configuration_0283 import (
    QdrantRealBindingConfigurationResult,
)
from inference.qdrant_scoped_executor_factory_0283 import (
    QdrantScopedExecutorBinding,
    QdrantScopedExecutorFactoryError,
    QdrantScopedExecutorFactoryPolicy,
    build_qdrant_scoped_executor_binding,
)


CONTROLLED_SCHEDULER_PROJECTION_BINDING_SCHEMA = (
    "missipy.qdrant.controlled_scheduler_projection_binding.v1"
)


@dataclass(frozen=True, slots=True)
class QdrantControlledSchedulerProjectionCommand:
    embedding_report: Mapping[str, Any]
    configuration: QdrantRealBindingConfigurationResult
    execute: bool = False


@dataclass(frozen=True, slots=True)
class QdrantControlledSchedulerProjectionPolicy:
    require_projection_only: bool = True
    require_0262_default_projection_policy: bool = True
    close_binding: bool = True


@dataclass(frozen=True, slots=True)
class QdrantControlledSchedulerProjectionResult:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    dry_run: bool
    binding_ref: str
    policy_decision_id: str
    projection_request: Mapping[str, Any] = field(
        default_factory=dict
    )
    factory_report: Mapping[str, Any] = field(
        default_factory=dict
    )
    usage_result: Mapping[str, Any] = field(
        default_factory=dict
    )
    binding_constructed: bool = False
    binding_closed: bool = False
    qdrant_write_performed: bool = False
    boundaries: tuple[tuple[str, bool], ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                CONTROLLED_SCHEDULER_PROJECTION_BINDING_SCHEMA
            ),
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "dry_run": self.dry_run,
            "binding_ref": self.binding_ref,
            "policy_decision_id": self.policy_decision_id,
            "projection_request": dict(self.projection_request),
            "factory_report": dict(self.factory_report),
            "usage_result": dict(self.usage_result),
            "binding_constructed": self.binding_constructed,
            "binding_closed": self.binding_closed,
            "qdrant_write_performed": (
                self.qdrant_write_performed
            ),
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"qdrant_scheduler_projection_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"binding_constructed={self.binding_constructed}",
                f"binding_closed={self.binding_closed}",
                f"qdrant_write_performed={self.qdrant_write_performed}",
            )
        )


def run_qdrant_controlled_scheduler_projection_binding(
    command: QdrantControlledSchedulerProjectionCommand,
    policy: QdrantControlledSchedulerProjectionPolicy | None = None,
    *,
    factory_policy: QdrantScopedExecutorFactoryPolicy | None = None,
    binding_builder: Callable[
        ...,
        QdrantScopedExecutorBinding,
    ] = build_qdrant_scoped_executor_binding,
    projection_runner: Callable[
        ...,
        SchedulerManagedEmbeddingQdrantProjectionResult,
    ] = run_scheduler_managed_embedding_qdrant_projection_usage,
) -> QdrantControlledSchedulerProjectionResult:
    """Preview or execute the existing 0262 projection path."""

    active_policy = (
        policy or QdrantControlledSchedulerProjectionPolicy()
    )
    configuration = command.configuration
    issues = _validate_binding_configuration(
        configuration,
        active_policy,
    )
    request = SchedulerManagedEmbeddingQdrantProjectionRequest(
        policy_decision_id=(
            configuration.effect_gate.policy_decision_id
        ),
        collection_name=configuration.target.collection_name,
        vector_dimension=configuration.target.vector_dimension,
    )

    if issues:
        return _result(
            command,
            request,
            issues=tuple(issues),
        )

    if not command.execute:
        usage = projection_runner(
            command.embedding_report,
            request,
            execute=False,
            executor=None,
        )
        return _result(
            command,
            request,
            issues=tuple(usage.issues),
            usage=usage,
            qdrant_write_performed=False,
        )

    binding: QdrantScopedExecutorBinding | None = None
    usage: SchedulerManagedEmbeddingQdrantProjectionResult | None = None
    factory_report: Mapping[str, Any] = {}
    binding_constructed = False
    binding_closed = False
    execution_issues: list[str] = []

    try:
        binding = binding_builder(
            configuration,
            factory_policy,
        )
        binding_constructed = True
        factory_report = binding.report.to_json_dict()
        usage = projection_runner(
            command.embedding_report,
            request,
            execute=True,
            executor=binding.executor,
        )
        execution_issues.extend(usage.issues)
    except QdrantScopedExecutorFactoryError as exc:
        factory_report = exc.report.to_json_dict()
        execution_issues.extend(exc.report.issues)
    except Exception as exc:
        execution_issues.append(
            "controlled projection execution failed: "
            f"{type(exc).__name__}: {_safe_message(exc)}"
        )
    finally:
        if binding is not None and active_policy.close_binding:
            try:
                binding.close()
                binding_closed = True
            except Exception as exc:
                execution_issues.append(
                    "scoped binding close failed: "
                    f"{type(exc).__name__}: {_safe_message(exc)}"
                )

    write_performed = bool(
        usage is not None
        and usage.valid
        and usage.execute
        and usage.write_result
    )
    return _result(
        command,
        request,
        issues=tuple(execution_issues),
        factory_report=factory_report,
        usage=usage,
        binding_constructed=binding_constructed,
        binding_closed=binding_closed,
        qdrant_write_performed=write_performed,
    )


def _validate_binding_configuration(
    configuration: QdrantRealBindingConfigurationResult,
    policy: QdrantControlledSchedulerProjectionPolicy,
) -> list[str]:
    issues: list[str] = []

    if not configuration.valid:
        issues.append("binding configuration must be valid")
    if not configuration.binding_ref:
        issues.append("binding configuration ref is required")
    if "projection" not in configuration.requested_operations:
        issues.append(
            "binding configuration must request projection"
        )
    if (
        policy.require_projection_only
        and configuration.requested_operations != ("projection",)
    ):
        issues.append(
            "controlled projection requires projection-only binding"
        )
    if not configuration.effect_gate.allow_write:
        issues.append(
            "projection binding requires allow_write effect gate"
        )
    if (
        policy.require_projection_only
        and configuration.effect_gate.allow_search
    ):
        issues.append(
            "projection-only binding must not allow search"
        )
    if not configuration.effect_gate.policy_decision_id:
        issues.append(
            "projection binding requires policy_decision_id"
        )
    if (
        policy.require_0262_default_projection_policy
        and configuration.projection_policy
        != QdrantProjectionPolicy()
    ):
        issues.append(
            "0262 currently requires its default projection policy"
        )
    return issues


def _result(
    command: QdrantControlledSchedulerProjectionCommand,
    request: SchedulerManagedEmbeddingQdrantProjectionRequest,
    *,
    issues: tuple[str, ...],
    factory_report: Mapping[str, Any] | None = None,
    usage: (
        SchedulerManagedEmbeddingQdrantProjectionResult | None
    ) = None,
    binding_constructed: bool = False,
    binding_closed: bool = False,
    qdrant_write_performed: bool = False,
) -> QdrantControlledSchedulerProjectionResult:
    usage_mapping = usage.to_mapping() if usage is not None else {}
    valid = not issues and bool(
        usage is not None and usage.valid
    )
    return QdrantControlledSchedulerProjectionResult(
        valid=valid,
        issues=issues,
        execute=command.execute,
        dry_run=not command.execute,
        binding_ref=command.configuration.binding_ref,
        policy_decision_id=(
            command.configuration.effect_gate.policy_decision_id
        ),
        projection_request=request.to_mapping(),
        factory_report=dict(factory_report or {}),
        usage_result=usage_mapping,
        binding_constructed=binding_constructed,
        binding_closed=binding_closed,
        qdrant_write_performed=qdrant_write_performed,
        boundaries=_boundaries(),
    )


def _safe_message(exc: Exception) -> str:
    text = str(exc).strip() or type(exc).__name__
    return text[:300]


def _boundaries() -> tuple[tuple[str, bool], ...]:
    return (
        ("existing_0262_usage_reused", True),
        ("existing_r3_factory_reused", True),
        ("scheduler_owned_usage_preserved", True),
        ("preview_constructs_client", False),
        ("qdrant_write_requires_execute", True),
        ("new_scheduler_added", False),
        ("scheduler_run_modified", False),
        ("new_qdrant_executor_added", False),
        ("new_transport_added", False),
        ("control_proxy_integrated", False),
        ("event_bus_integrated", False),
        ("shm_or_mmio_integrated", False),
        ("sql_write_performed", False),
        ("projects_repository_change_required", False),
    )
