from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from inference.qdrant_client_projection_executor import (
    QdrantClientDependencyReadiness,
    QdrantClientExecutionError,
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
)
from inference.qdrant_projection_adapter import (
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
)
from inference.qdrant_real_binding_configuration_0283 import (
    QdrantRealBindingConfigurationCommand,
    build_qdrant_real_binding_configuration,
)
from inference.qdrant_scoped_executor_factory_0283 import (
    QdrantScopedExecutorBinding,
    QdrantScopedExecutorFactoryError,
    QdrantScopedExecutorFactoryPolicy,
    build_qdrant_scoped_executor_binding,
    inspect_qdrant_scoped_executor_factory,
)
from inference.qdrant_sql_authority_scope import (
    QdrantSqlAuthorityScope,
    QdrantStrictGrpcTransportPolicy,
)


class FakeClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.close_count = 0
        self.upsert_count = 0
        self.query_count = 0

    def close(self):
        self.close_count += 1

    def upsert(self, **kwargs):
        self.upsert_count += 1
        raise AssertionError("factory must not upsert")

    def query_points(self, **kwargs):
        self.query_count += 1
        raise AssertionError("factory must not search")


class FakeModels:
    class PointStruct:
        def __init__(self, **kwargs):
            self.kwargs = kwargs


def _readiness(*, installed=True, version="1.18.0"):
    return QdrantClientDependencyReadiness(
        installed=installed,
        version=version,
    )


def _configuration(*, operations=("projection", "recall"), api_key_env_var=""):
    return build_qdrant_real_binding_configuration(
        QdrantRealBindingConfigurationCommand(
            connection=QdrantClientConnectionConfig(
                url="http://127.0.0.1:6333",
                timeout_seconds=10.0,
                prefer_grpc=True,
                grpc_port=6334,
                wait_for_write=True,
                check_compatibility=True,
            ),
            effect_gate=QdrantClientEffectGate(
                policy_decision_id="policy:0283:r3",
                allow_write="projection" in operations,
                allow_search="recall" in operations,
            ),
            sql_authority_scope=QdrantSqlAuthorityScope(
                authority_ref="sql-authority:sqlite:fixture",
                store_kind="sqlite",
            ),
            transport_policy=QdrantStrictGrpcTransportPolicy(),
            target=QdrantProjectionTarget(
                collection_name="autodoc_context_embeddings",
                vector_dimension=384,
            ),
            projection_policy=QdrantProjectionPolicy(),
            requested_operations=operations,
            api_key_env_var=api_key_env_var,
            recall_oversample_factor=4,
        )
    )


def test_inspection_is_read_only_and_does_not_construct_client():
    report = inspect_qdrant_scoped_executor_factory(
        _configuration(),
        dependency_inspector=lambda: _readiness(),
    )
    assert report.valid is True
    assert report.client_constructed is False
    assert report.data_operation_performed is False


def test_factory_reuses_concrete_builder_and_sql_scope():
    created = []

    def client_factory(**kwargs):
        client = FakeClient(**kwargs)
        created.append(client)
        return client

    binding = build_qdrant_scoped_executor_binding(
        _configuration(),
        dependency_inspector=lambda: _readiness(),
        environment={},
        client_factory=client_factory,
        models_module=FakeModels,
    )
    assert isinstance(binding, QdrantScopedExecutorBinding)
    assert binding.report.client_constructed is True
    assert binding.executor.scope.authority_ref == "sql-authority:sqlite:fixture"
    assert created[0].kwargs["prefer_grpc"] is True
    assert created[0].kwargs["grpc_port"] == 6334
    assert created[0].upsert_count == 0
    assert created[0].query_count == 0


def test_binding_close_delegates_to_existing_client():
    clients = []

    def client_factory(**kwargs):
        client = FakeClient(**kwargs)
        clients.append(client)
        return client

    binding = build_qdrant_scoped_executor_binding(
        _configuration(),
        dependency_inspector=lambda: _readiness(),
        client_factory=client_factory,
        models_module=FakeModels,
    )
    binding.close()
    assert clients[0].close_count == 1


def test_empty_requested_operations_are_rejected_before_client():
    called = False

    def client_factory(**kwargs):
        nonlocal called
        called = True
        return FakeClient(**kwargs)

    with pytest.raises(QdrantScopedExecutorFactoryError) as captured:
        build_qdrant_scoped_executor_binding(
            _configuration(operations=()),
            dependency_inspector=lambda: _readiness(),
            client_factory=client_factory,
            models_module=FakeModels,
        )
    assert called is False
    assert any("at least one requested operation" in x for x in captured.value.report.issues)


def test_invalid_dependency_is_rejected_before_client():
    called = False

    def client_factory(**kwargs):
        nonlocal called
        called = True
        return FakeClient(**kwargs)

    with pytest.raises(QdrantScopedExecutorFactoryError) as captured:
        build_qdrant_scoped_executor_binding(
            _configuration(),
            dependency_inspector=lambda: _readiness(version="1.17.0"),
            client_factory=client_factory,
            models_module=FakeModels,
        )
    assert called is False
    assert captured.value.report.dependency_valid is False


def test_environment_secret_is_loaded_but_never_serialized():
    observed = {}

    def client_factory(**kwargs):
        observed.update(kwargs)
        return FakeClient(**kwargs)

    binding = build_qdrant_scoped_executor_binding(
        _configuration(api_key_env_var="QDRANT_API_KEY"),
        dependency_inspector=lambda: _readiness(),
        environment={"QDRANT_API_KEY": "top-secret"},
        client_factory=client_factory,
        models_module=FakeModels,
    )
    assert observed["api_key"] == "top-secret"
    payload = binding.report.to_json_dict()
    assert "top-secret" not in repr(payload)
    assert payload["api_key"]["secret_value_serialized"] is False


def test_missing_environment_secret_is_rejected():
    with pytest.raises(QdrantScopedExecutorFactoryError) as captured:
        build_qdrant_scoped_executor_binding(
            _configuration(api_key_env_var="QDRANT_API_KEY"),
            dependency_inspector=lambda: _readiness(),
            environment={},
            client_factory=FakeClient,
            models_module=FakeModels,
        )
    assert any("environment variable is missing or empty" in x for x in captured.value.report.issues)


def test_secret_resolution_can_be_forbidden():
    report = inspect_qdrant_scoped_executor_factory(
        _configuration(api_key_env_var="QDRANT_API_KEY"),
        QdrantScopedExecutorFactoryPolicy(allow_environment_secret_resolution=False),
        dependency_inspector=lambda: _readiness(),
        environment={"QDRANT_API_KEY": "top-secret"},
    )
    assert report.valid is False
    assert any("secret resolution is forbidden" in x for x in report.issues)


def test_builder_failure_is_wrapped_in_secret_free_report():
    def failing_factory(**kwargs):
        raise RuntimeError("client construction refused")

    with pytest.raises(QdrantScopedExecutorFactoryError) as captured:
        build_qdrant_scoped_executor_binding(
            _configuration(),
            dependency_inspector=lambda: _readiness(),
            client_factory=failing_factory,
            models_module=FakeModels,
        )
    assert captured.value.report.client_constructed is False
    assert any("construction failed" in x for x in captured.value.report.issues)


def test_existing_effect_gate_remains_effective_after_composition():
    binding = build_qdrant_scoped_executor_binding(
        _configuration(operations=("recall",)),
        dependency_inspector=lambda: _readiness(),
        client_factory=FakeClient,
        models_module=FakeModels,
    )
    with pytest.raises(QdrantClientExecutionError) as captured:
        binding.executor.upsert_points(
            (),
            target=binding.configuration.target,
            policy=binding.configuration.projection_policy,
        )
    assert captured.value.failure.category == "gate_denied"


def test_contracts_are_frozen():
    report = inspect_qdrant_scoped_executor_factory(
        _configuration(),
        dependency_inspector=lambda: _readiness(),
    )
    policy = QdrantScopedExecutorFactoryPolicy()
    with pytest.raises(FrozenInstanceError):
        report.valid = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        policy.require_dependency_readiness = False  # type: ignore[misc]
