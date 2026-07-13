"""Scoped real-Qdrant executor factory composition for phase 0283-r3.

This module reuses the existing qdrant-client executor factory and immediately
wraps its result with the existing SQL-authority scope. It adds no Qdrant
executor, transport, Scheduler path, ControlProxy path, EventBus path, shared
memory path or hardware path.

Client construction is an explicit I/O boundary. The composition itself never
calls ``upsert_points`` or ``search_vector``.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from types import ModuleType
from typing import Any, Callable, Mapping

from inference.qdrant_client_projection_executor import (
    QdrantClientDependencyReadiness,
    QdrantClientProjectionExecutor,
    build_qdrant_client_projection_executor,
    inspect_qdrant_client_dependency,
)
from inference.qdrant_real_binding_configuration_0283 import (
    QdrantRealBindingConfigurationResult,
)
from inference.qdrant_sql_authority_scope import (
    SqlAuthorityScopedQdrantExecutor,
)


SCOPED_EXECUTOR_FACTORY_REPORT_SCHEMA = (
    "missipy.qdrant.scoped_executor_factory_report.v1"
)


@dataclass(frozen=True, slots=True)
class QdrantScopedExecutorFactoryPolicy:
    require_valid_configuration: bool = True
    require_requested_operations: bool = True
    require_dependency_readiness: bool = True
    allow_environment_secret_resolution: bool = True


@dataclass(frozen=True, slots=True)
class QdrantScopedExecutorFactoryReport:
    valid: bool
    issues: tuple[str, ...]
    binding_ref: str
    requested_operations: tuple[str, ...]
    dependency_installed: bool
    dependency_version: str
    dependency_required_version: str
    dependency_valid: bool
    api_key_source: str
    api_key_loaded: bool
    client_constructed: bool
    concrete_executor_reused: bool
    sql_scope_wrapper_reused: bool
    data_operation_performed: bool
    boundaries: tuple[tuple[str, bool], ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": SCOPED_EXECUTOR_FACTORY_REPORT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "binding_ref": self.binding_ref,
            "requested_operations": list(self.requested_operations),
            "dependency": {
                "installed": self.dependency_installed,
                "version": self.dependency_version,
                "required_version": self.dependency_required_version,
                "valid": self.dependency_valid,
            },
            "api_key": {
                "source": self.api_key_source,
                "loaded": self.api_key_loaded,
                "secret_value_serialized": False,
            },
            "client_constructed": self.client_constructed,
            "concrete_executor_reused": self.concrete_executor_reused,
            "sql_scope_wrapper_reused": self.sql_scope_wrapper_reused,
            "data_operation_performed": self.data_operation_performed,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        operations = ",".join(self.requested_operations)
        return " ".join(
            (
                f"qdrant_scoped_factory_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"operations={operations or '-'}",
                f"dependency_valid={self.dependency_valid}",
                f"client_constructed={self.client_constructed}",
                "data_operation_performed=False",
            )
        )


@dataclass(frozen=True, slots=True)
class QdrantScopedExecutorBinding:
    configuration: QdrantRealBindingConfigurationResult
    executor: SqlAuthorityScopedQdrantExecutor
    delegate: QdrantClientProjectionExecutor
    report: QdrantScopedExecutorFactoryReport

    def close(self) -> None:
        self.executor.close()


class QdrantScopedExecutorFactoryError(RuntimeError):
    """Failure carrying a secret-free serializable report."""

    def __init__(self, report: QdrantScopedExecutorFactoryReport) -> None:
        self.report = report
        message = "; ".join(report.issues) or "factory failed"
        super().__init__(message)


def inspect_qdrant_scoped_executor_factory(
    configuration: QdrantRealBindingConfigurationResult,
    policy: QdrantScopedExecutorFactoryPolicy | None = None,
    *,
    dependency_inspector: Callable[[], QdrantClientDependencyReadiness] = (
        inspect_qdrant_client_dependency
    ),
    environment: Mapping[str, str] | None = None,
) -> QdrantScopedExecutorFactoryReport:
    """Validate construction readiness without building a client."""

    active_policy = policy or QdrantScopedExecutorFactoryPolicy()
    readiness = dependency_inspector()
    issues, api_key_loaded = _factory_issues(
        configuration,
        active_policy,
        readiness,
        environment,
    )
    return _report(
        configuration,
        readiness,
        issues=issues,
        api_key_loaded=api_key_loaded,
        client_constructed=False,
    )


def build_qdrant_scoped_executor_binding(
    configuration: QdrantRealBindingConfigurationResult,
    policy: QdrantScopedExecutorFactoryPolicy | None = None,
    *,
    dependency_inspector: Callable[[], QdrantClientDependencyReadiness] = (
        inspect_qdrant_client_dependency
    ),
    environment: Mapping[str, str] | None = None,
    client_factory: Callable[..., Any] | None = None,
    models_module: ModuleType | Any | None = None,
    executor_builder: Callable[..., QdrantClientProjectionExecutor] = (
        build_qdrant_client_projection_executor
    ),
) -> QdrantScopedExecutorBinding:
    """Build and scope the existing concrete executor without a data call."""

    active_policy = policy or QdrantScopedExecutorFactoryPolicy()
    readiness = dependency_inspector()
    issues, api_key_loaded = _factory_issues(
        configuration,
        active_policy,
        readiness,
        environment,
    )
    if issues:
        raise QdrantScopedExecutorFactoryError(
            _report(
                configuration,
                readiness,
                issues=issues,
                api_key_loaded=api_key_loaded,
                client_constructed=False,
            )
        )

    api_key = _resolve_api_key(configuration, active_policy, environment)
    try:
        delegate = executor_builder(
            configuration.connection,
            configuration.effect_gate,
            api_key=api_key,
            client_factory=client_factory,
            models_module=models_module,
        )
    except Exception as exc:
        report = _report(
            configuration,
            readiness,
            issues=(
                "concrete executor construction failed: "
                f"{type(exc).__name__}: {_safe_message(exc)}",
            ),
            api_key_loaded=bool(api_key),
            client_constructed=False,
        )
        raise QdrantScopedExecutorFactoryError(report) from exc

    scoped = SqlAuthorityScopedQdrantExecutor(
        delegate,
        configuration.sql_authority_scope,
        recall_oversample_factor=configuration.recall_oversample_factor,
    )
    report = _report(
        configuration,
        readiness,
        issues=(),
        api_key_loaded=bool(api_key),
        client_constructed=True,
    )
    return QdrantScopedExecutorBinding(
        configuration=configuration,
        executor=scoped,
        delegate=delegate,
        report=report,
    )


def _factory_issues(
    configuration: QdrantRealBindingConfigurationResult,
    policy: QdrantScopedExecutorFactoryPolicy,
    readiness: QdrantClientDependencyReadiness,
    environment: Mapping[str, str] | None,
) -> tuple[tuple[str, ...], bool]:
    issues: list[str] = []

    if policy.require_valid_configuration:
        if not configuration.valid:
            issues.append("binding configuration must be valid")
        if not configuration.binding_ref:
            issues.append("binding configuration ref is required")

    if policy.require_requested_operations and not configuration.requested_operations:
        issues.append("at least one requested operation is required")

    if policy.require_dependency_readiness and not readiness.valid:
        issues.append("qdrant-client dependency readiness is invalid")

    api_key_loaded = False
    if configuration.api_key_env_var:
        if not policy.allow_environment_secret_resolution:
            issues.append("environment secret resolution is forbidden")
        else:
            source = environment if environment is not None else os.environ
            api_key_loaded = bool(
                str(source.get(configuration.api_key_env_var, "")).strip()
            )
            if not api_key_loaded:
                issues.append(
                    "configured Qdrant API key environment variable is missing or empty"
                )

    return tuple(issues), api_key_loaded


def _resolve_api_key(
    configuration: QdrantRealBindingConfigurationResult,
    policy: QdrantScopedExecutorFactoryPolicy,
    environment: Mapping[str, str] | None,
) -> str | None:
    if not configuration.api_key_env_var:
        return None
    if not policy.allow_environment_secret_resolution:
        return None
    source = environment if environment is not None else os.environ
    value = str(source.get(configuration.api_key_env_var, "")).strip()
    return value or None


def _report(
    configuration: QdrantRealBindingConfigurationResult,
    readiness: QdrantClientDependencyReadiness,
    *,
    issues: tuple[str, ...],
    api_key_loaded: bool,
    client_constructed: bool,
) -> QdrantScopedExecutorFactoryReport:
    return QdrantScopedExecutorFactoryReport(
        valid=not issues,
        issues=issues,
        binding_ref=configuration.binding_ref,
        requested_operations=configuration.requested_operations,
        dependency_installed=readiness.installed,
        dependency_version=readiness.version,
        dependency_required_version=readiness.required_version,
        dependency_valid=readiness.valid,
        api_key_source=(
            "environment" if configuration.api_key_env_var else "none"
        ),
        api_key_loaded=api_key_loaded,
        client_constructed=client_constructed,
        concrete_executor_reused=True,
        sql_scope_wrapper_reused=True,
        data_operation_performed=False,
        boundaries=_boundaries(),
    )


def _safe_message(exc: Exception) -> str:
    text = str(exc).strip() or type(exc).__name__
    return text[:300]


def _boundaries() -> tuple[tuple[str, bool], ...]:
    return (
        ("existing_client_factory_reused", True),
        ("existing_concrete_executor_reused", True),
        ("existing_sql_scope_wrapper_reused", True),
        ("new_qdrant_executor_added", False),
        ("new_transport_added", False),
        ("scheduler_path_added", False),
        ("control_proxy_path_added", False),
        ("event_bus_path_added", False),
        ("shm_or_mmio_path_added", False),
        ("secret_value_serialized", False),
        ("data_operation_performed", False),
        ("qdrant_write_performed", False),
        ("qdrant_search_performed", False),
        ("sql_write_performed", False),
        ("projects_repository_change_required", False),
    )
