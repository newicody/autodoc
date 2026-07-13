"""Controlled Scheduler-owned Qdrant recall and SQL rehydrate binding. 0283-r5.

This module binds the existing 0263 recall/rehydration use case to the existing
0283-r3 scoped executor factory. Preview does not construct a client and does
not read SQL. Execute performs one controlled Qdrant recall, keeps reference-only
hits, rehydrates through the injected existing SQL store and closes the binding.

No Scheduler.run modification, alternate executor, transport, ControlProxy,
EventBus, shared-memory or hardware path is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from context.scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263 import (
    SchedulerManagedQdrantRecallSqlRehydrateRequest,
    SchedulerManagedQdrantRecallSqlRehydrateResult,
    default_query_ref_from_embedding_report,
    run_scheduler_managed_qdrant_recall_sql_rehydrate_usage,
)
from inference.qdrant_real_binding_configuration_0283 import (
    QdrantRealBindingConfigurationResult,
)
from inference.qdrant_scoped_executor_factory_0283 import (
    QdrantScopedExecutorBinding,
    QdrantScopedExecutorFactoryError,
    QdrantScopedExecutorFactoryPolicy,
    build_qdrant_scoped_executor_binding,
)


CONTROLLED_SCHEDULER_RECALL_BINDING_SCHEMA = (
    "missipy.qdrant.controlled_scheduler_recall_binding.v1"
)


@dataclass(frozen=True, slots=True)
class QdrantControlledSchedulerRecallCommand:
    embedding_report: Mapping[str, Any]
    store: Any
    configuration: QdrantRealBindingConfigurationResult
    query_ref: str = ""
    limit: int = 8
    execute: bool = False


@dataclass(frozen=True, slots=True)
class QdrantControlledSchedulerRecallPolicy:
    require_recall_only: bool = True
    require_limit_within_configured_policy: bool = True
    close_binding: bool = True


@dataclass(frozen=True, slots=True)
class QdrantControlledSchedulerRecallResult:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    dry_run: bool
    binding_ref: str
    policy_decision_id: str
    recall_request: Mapping[str, Any] = field(
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
    qdrant_search_performed: bool = False
    sql_rehydrate_attempted: bool = False
    boundaries: tuple[tuple[str, bool], ...] = ()

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": CONTROLLED_SCHEDULER_RECALL_BINDING_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "dry_run": self.dry_run,
            "binding_ref": self.binding_ref,
            "policy_decision_id": self.policy_decision_id,
            "recall_request": dict(self.recall_request),
            "factory_report": dict(self.factory_report),
            "usage_result": dict(self.usage_result),
            "binding_constructed": self.binding_constructed,
            "binding_closed": self.binding_closed,
            "qdrant_search_performed": (
                self.qdrant_search_performed
            ),
            "sql_rehydrate_attempted": (
                self.sql_rehydrate_attempted
            ),
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"qdrant_scheduler_recall_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"binding_constructed={self.binding_constructed}",
                f"binding_closed={self.binding_closed}",
                f"qdrant_search_performed={self.qdrant_search_performed}",
                f"sql_rehydrate_attempted={self.sql_rehydrate_attempted}",
            )
        )


def run_qdrant_controlled_scheduler_recall_binding(
    command: QdrantControlledSchedulerRecallCommand,
    policy: QdrantControlledSchedulerRecallPolicy | None = None,
    *,
    factory_policy: QdrantScopedExecutorFactoryPolicy | None = None,
    binding_builder: Callable[
        ...,
        QdrantScopedExecutorBinding,
    ] = build_qdrant_scoped_executor_binding,
    recall_runner: Callable[
        ...,
        SchedulerManagedQdrantRecallSqlRehydrateResult,
    ] = run_scheduler_managed_qdrant_recall_sql_rehydrate_usage,
) -> QdrantControlledSchedulerRecallResult:
    """Preview or execute the existing 0263 recall/rehydrate path."""

    active_policy = (
        policy or QdrantControlledSchedulerRecallPolicy()
    )
    configuration = command.configuration
    query_ref = (
        command.query_ref.strip()
        or default_query_ref_from_embedding_report(
            command.embedding_report
        )
    )
    request = SchedulerManagedQdrantRecallSqlRehydrateRequest(
        query_ref=query_ref,
        policy_decision_id=(
            configuration.effect_gate.policy_decision_id
        ),
        collection_name=configuration.target.collection_name,
        vector_dimension=configuration.target.vector_dimension,
        limit=command.limit,
    )
    issues = _validate_binding_configuration(
        configuration,
        request,
        active_policy,
    )
    if issues:
        return _result(
            command,
            request,
            issues=tuple(issues),
        )

    if not command.execute:
        usage = recall_runner(
            command.embedding_report,
            command.store,
            request,
            execute=False,
            executor=None,
        )
        return _result(
            command,
            request,
            issues=tuple(usage.issues),
            usage=usage,
        )

    binding: QdrantScopedExecutorBinding | None = None
    usage: SchedulerManagedQdrantRecallSqlRehydrateResult | None = None
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
        usage = recall_runner(
            command.embedding_report,
            command.store,
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
            "controlled recall execution failed: "
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

    search_performed = bool(
        usage is not None
        and usage.valid
        and usage.execute
        and usage.recall
    )
    return _result(
        command,
        request,
        issues=tuple(execution_issues),
        factory_report=factory_report,
        usage=usage,
        binding_constructed=binding_constructed,
        binding_closed=binding_closed,
        qdrant_search_performed=search_performed,
        sql_rehydrate_attempted=search_performed,
    )


def _validate_binding_configuration(
    configuration: QdrantRealBindingConfigurationResult,
    request: SchedulerManagedQdrantRecallSqlRehydrateRequest,
    policy: QdrantControlledSchedulerRecallPolicy,
) -> list[str]:
    issues: list[str] = []

    if not configuration.valid:
        issues.append("binding configuration must be valid")
    if not configuration.binding_ref:
        issues.append("binding configuration ref is required")
    if "recall" not in configuration.requested_operations:
        issues.append(
            "binding configuration must request recall"
        )
    if (
        policy.require_recall_only
        and configuration.requested_operations != ("recall",)
    ):
        issues.append(
            "controlled recall requires recall-only binding"
        )
    if not configuration.effect_gate.allow_search:
        issues.append(
            "recall binding requires allow_search effect gate"
        )
    if (
        policy.require_recall_only
        and configuration.effect_gate.allow_write
    ):
        issues.append(
            "recall-only binding must not allow write"
        )
    if not configuration.effect_gate.policy_decision_id:
        issues.append(
            "recall binding requires policy_decision_id"
        )
    if request.limit <= 0:
        issues.append("recall limit must be > 0")
    if (
        policy.require_limit_within_configured_policy
        and request.limit
        > configuration.projection_policy.max_recall_hits
    ):
        issues.append(
            "recall limit exceeds configured max_recall_hits"
        )
    return issues


def _result(
    command: QdrantControlledSchedulerRecallCommand,
    request: SchedulerManagedQdrantRecallSqlRehydrateRequest,
    *,
    issues: tuple[str, ...],
    factory_report: Mapping[str, Any] | None = None,
    usage: SchedulerManagedQdrantRecallSqlRehydrateResult | None = None,
    binding_constructed: bool = False,
    binding_closed: bool = False,
    qdrant_search_performed: bool = False,
    sql_rehydrate_attempted: bool = False,
) -> QdrantControlledSchedulerRecallResult:
    usage_mapping = usage.to_mapping() if usage is not None else {}
    valid = not issues and bool(
        usage is not None and usage.valid
    )
    return QdrantControlledSchedulerRecallResult(
        valid=valid,
        issues=issues,
        execute=command.execute,
        dry_run=not command.execute,
        binding_ref=command.configuration.binding_ref,
        policy_decision_id=(
            command.configuration.effect_gate.policy_decision_id
        ),
        recall_request=request.to_mapping(),
        factory_report=dict(factory_report or {}),
        usage_result=usage_mapping,
        binding_constructed=binding_constructed,
        binding_closed=binding_closed,
        qdrant_search_performed=qdrant_search_performed,
        sql_rehydrate_attempted=sql_rehydrate_attempted,
        boundaries=_boundaries(),
    )


def _safe_message(exc: Exception) -> str:
    text = str(exc).strip() or type(exc).__name__
    return text[:300]


def _boundaries() -> tuple[tuple[str, bool], ...]:
    return (
        ("existing_0263_usage_reused", True),
        ("existing_r3_factory_reused", True),
        ("existing_sql_store_reused", True),
        ("scheduler_owned_usage_preserved", True),
        ("preview_constructs_client", False),
        ("preview_reads_sql", False),
        ("qdrant_search_requires_execute", True),
        ("qdrant_returns_refs_only", True),
        ("sql_remains_authority", True),
        ("new_scheduler_added", False),
        ("scheduler_run_modified", False),
        ("new_qdrant_executor_added", False),
        ("new_transport_added", False),
        ("control_proxy_integrated", False),
        ("event_bus_integrated", False),
        ("shm_or_mmio_integrated", False),
        ("qdrant_write_performed", False),
        ("sql_write_performed", False),
        ("projects_repository_change_required", False),
    )
