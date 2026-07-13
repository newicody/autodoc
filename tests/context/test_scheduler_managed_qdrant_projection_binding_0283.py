from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from typing import Any

import pytest

from context.scheduler_managed_qdrant_projection_binding_0283 import (
    QdrantControlledSchedulerProjectionCommand,
    QdrantControlledSchedulerProjectionPolicy,
    run_qdrant_controlled_scheduler_projection_binding,
)
from inference.qdrant_client_projection_executor import (
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
)
from inference.qdrant_projection_adapter import (
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
    QdrantProjectionWriteResult,
)
from inference.qdrant_real_binding_configuration_0283 import (
    QdrantRealBindingConfigurationCommand,
    build_qdrant_real_binding_configuration,
)
from inference.qdrant_scoped_executor_factory_0283 import (
    QdrantScopedExecutorFactoryError,
    QdrantScopedExecutorFactoryReport,
)
from inference.qdrant_sql_authority_scope import (
    QdrantSqlAuthorityScope,
    QdrantStrictGrpcTransportPolicy,
)


def _embedding_report() -> dict[str, Any]:
    return {
        "embedding": {
            "sql_ref": "sql:context:15",
            "embedding_ref": "embedding:e5:15",
            "source_ref": "ctx-fragment:sql:context:15",
            "vector": [1.0] + [0.0] * 383,
            "dimension": 384,
            "normalized": True,
            "backend_ref": "openvino:model:multilingual-e5-small",
            "role": "passage",
            "metadata": {
                "context_ref": "sql:context:15",
                "device": "CPU",
            },
        }
    }


def _configuration(
    *,
    operations=("projection",),
    projection_policy=None,
):
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
                policy_decision_id="policy:0283:r4",
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
            projection_policy=(
                projection_policy or QdrantProjectionPolicy()
            ),
            requested_operations=operations,
        )
    )


class FakeExecutor:
    def __init__(self):
        self.upsert_count = 0

    def upsert_points(self, points, *, target, policy):
        self.upsert_count += 1
        return QdrantProjectionWriteResult(
            target=target,
            point_ids=tuple(point.point_id for point in points),
            acknowledged=True,
        )


@dataclass
class FakeFactoryReport:
    def to_json_dict(self):
        return {
            "schema": "fake-factory-report",
            "valid": True,
            "client_constructed": True,
        }


class FakeBinding:
    def __init__(self, *, close_error: Exception | None = None):
        self.executor = FakeExecutor()
        self.report = FakeFactoryReport()
        self.close_count = 0
        self.close_error = close_error

    def close(self):
        self.close_count += 1
        if self.close_error is not None:
            raise self.close_error


def test_preview_reuses_0262_without_constructing_binding():
    calls = []

    def forbidden_builder(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("preview must not construct a client")

    result = run_qdrant_controlled_scheduler_projection_binding(
        QdrantControlledSchedulerProjectionCommand(
            embedding_report=_embedding_report(),
            configuration=_configuration(),
            execute=False,
        ),
        binding_builder=forbidden_builder,
    )

    assert result.valid is True
    assert calls == []
    assert result.dry_run is True
    assert result.binding_constructed is False
    assert result.binding_closed is False
    assert result.qdrant_write_performed is False
    assert result.usage_result["dry_run"] is True
    assert result.projection_request == {
        "policy_decision_id": "policy:0283:r4",
        "collection_name": "autodoc_context_embeddings",
        "vector_dimension": 384,
    }


def test_execute_builds_scoped_binding_injects_0262_and_closes():
    binding = FakeBinding()
    calls = []

    def builder(configuration, factory_policy):
        calls.append((configuration, factory_policy))
        return binding

    result = run_qdrant_controlled_scheduler_projection_binding(
        QdrantControlledSchedulerProjectionCommand(
            embedding_report=_embedding_report(),
            configuration=_configuration(),
            execute=True,
        ),
        binding_builder=builder,
    )

    assert result.valid is True
    assert len(calls) == 1
    assert binding.executor.upsert_count == 1
    assert binding.close_count == 1
    assert result.binding_constructed is True
    assert result.binding_closed is True
    assert result.qdrant_write_performed is True
    assert result.usage_result["execute"] is True
    assert result.usage_result["write_result"]["acknowledged"] is True


def test_combined_projection_recall_binding_is_rejected_by_default():
    called = False

    def builder(*args, **kwargs):
        nonlocal called
        called = True
        return FakeBinding()

    result = run_qdrant_controlled_scheduler_projection_binding(
        QdrantControlledSchedulerProjectionCommand(
            embedding_report=_embedding_report(),
            configuration=_configuration(
                operations=("projection", "recall")
            ),
            execute=True,
        ),
        binding_builder=builder,
    )

    assert result.valid is False
    assert called is False
    assert any(
        "projection-only binding" in issue
        for issue in result.issues
    )


def test_non_default_0262_policy_is_rejected_not_ignored():
    configuration = _configuration(
        projection_policy=QdrantProjectionPolicy(
            max_points=8,
        )
    )

    result = run_qdrant_controlled_scheduler_projection_binding(
        QdrantControlledSchedulerProjectionCommand(
            embedding_report=_embedding_report(),
            configuration=configuration,
            execute=False,
        )
    )

    assert result.valid is False
    assert (
        "0262 currently requires its default projection policy"
        in result.issues
    )


def test_invalid_embedding_is_reported_by_existing_0262_usage():
    result = run_qdrant_controlled_scheduler_projection_binding(
        QdrantControlledSchedulerProjectionCommand(
            embedding_report={"embedding": {}},
            configuration=_configuration(),
            execute=False,
        )
    )

    assert result.valid is False
    assert result.usage_result["valid"] is False
    assert any(
        "embedding mapping must not be empty" in issue
        for issue in result.issues
    )


def test_factory_error_is_serialized_without_data_operation():
    report = QdrantScopedExecutorFactoryReport(
        valid=False,
        issues=("dependency invalid",),
        binding_ref="qdrant-real-binding:test",
        requested_operations=("projection",),
        dependency_installed=False,
        dependency_version="",
        dependency_required_version="1.18.0",
        dependency_valid=False,
        api_key_source="none",
        api_key_loaded=False,
        client_constructed=False,
        concrete_executor_reused=True,
        sql_scope_wrapper_reused=True,
        data_operation_performed=False,
        boundaries=(),
    )

    def builder(*args, **kwargs):
        raise QdrantScopedExecutorFactoryError(report)

    result = run_qdrant_controlled_scheduler_projection_binding(
        QdrantControlledSchedulerProjectionCommand(
            embedding_report=_embedding_report(),
            configuration=_configuration(),
            execute=True,
        ),
        binding_builder=builder,
    )

    assert result.valid is False
    assert result.binding_constructed is False
    assert result.qdrant_write_performed is False
    assert result.factory_report["valid"] is False
    assert "dependency invalid" in result.issues


def test_close_failure_is_reported_after_successful_write():
    binding = FakeBinding(close_error=RuntimeError("close refused"))

    result = run_qdrant_controlled_scheduler_projection_binding(
        QdrantControlledSchedulerProjectionCommand(
            embedding_report=_embedding_report(),
            configuration=_configuration(),
            execute=True,
        ),
        binding_builder=lambda *args: binding,
    )

    assert result.valid is False
    assert result.binding_constructed is True
    assert result.binding_closed is False
    assert result.qdrant_write_performed is True
    assert any(
        "scoped binding close failed" in issue
        for issue in result.issues
    )


def test_boundaries_preserve_current_architecture():
    result = run_qdrant_controlled_scheduler_projection_binding(
        QdrantControlledSchedulerProjectionCommand(
            embedding_report=_embedding_report(),
            configuration=_configuration(),
        )
    )

    assert dict(result.boundaries) == {
        "existing_0262_usage_reused": True,
        "existing_r3_factory_reused": True,
        "scheduler_owned_usage_preserved": True,
        "preview_constructs_client": False,
        "qdrant_write_requires_execute": True,
        "new_scheduler_added": False,
        "scheduler_run_modified": False,
        "new_qdrant_executor_added": False,
        "new_transport_added": False,
        "control_proxy_integrated": False,
        "event_bus_integrated": False,
        "shm_or_mmio_integrated": False,
        "sql_write_performed": False,
        "projects_repository_change_required": False,
    }


def test_contracts_are_frozen():
    command = QdrantControlledSchedulerProjectionCommand(
        embedding_report=_embedding_report(),
        configuration=_configuration(),
    )
    policy = QdrantControlledSchedulerProjectionPolicy()

    with pytest.raises(FrozenInstanceError):
        command.execute = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        policy.close_binding = False  # type: ignore[misc]
