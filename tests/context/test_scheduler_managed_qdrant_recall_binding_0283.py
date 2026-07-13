from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from context.scheduler_managed_qdrant_recall_binding_0283 import (
    QdrantControlledSchedulerRecallCommand,
    QdrantControlledSchedulerRecallPolicy,
    run_qdrant_controlled_scheduler_recall_binding,
)
from inference.qdrant_client_projection_executor import (
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
)
from inference.qdrant_projection_adapter import (
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
    QdrantRecallHit,
    QdrantRecallResult,
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
            "embedding_ref": "embedding:e5-query:28",
            "vector": [1.0] + [0.0] * 383,
            "dimension": 384,
            "normalized": True,
            "role": "query",
        }
    }


def _configuration(
    *,
    operations=("recall",),
    max_recall_hits=32,
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
                policy_decision_id="policy:0283:r5",
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
            projection_policy=QdrantProjectionPolicy(
                max_recall_hits=max_recall_hits,
            ),
            requested_operations=operations,
        )
    )


class FakeStore:
    def __init__(self):
        self.calls = []

    def get_record(self, sql_ref):
        self.calls.append(sql_ref)
        if sql_ref == "sql:context:missing":
            return None
        return {
            "context_ref": sql_ref,
            "kind": "context",
            "body": f"body for {sql_ref}",
        }


class FakeRecallExecutor:
    def __init__(self):
        self.search_count = 0

    def search_vector(self, vector, *, target, policy, query):
        self.search_count += 1
        return QdrantRecallResult(
            target=target,
            query=query,
            hits=(
                QdrantRecallHit(
                    point_id="qdrant-point:1",
                    sql_context_ref="sql:context:1",
                    score=0.95,
                    source_ref="ctx-fragment:sql:context:1",
                    payload=(
                        ("sql_context_ref", "sql:context:1"),
                    ),
                ),
                QdrantRecallHit(
                    point_id="qdrant-point:missing",
                    sql_context_ref="sql:context:missing",
                    score=0.80,
                    source_ref="ctx-fragment:sql:context:missing",
                    payload=(
                        (
                            "sql_context_ref",
                            "sql:context:missing",
                        ),
                    ),
                ),
            ),
            capped=False,
        )


class FakeFactoryReport:
    def to_json_dict(self):
        return {
            "schema": "fake-factory-report",
            "valid": True,
            "client_constructed": True,
        }


class FakeBinding:
    def __init__(self, *, close_error=None):
        self.executor = FakeRecallExecutor()
        self.report = FakeFactoryReport()
        self.close_count = 0
        self.close_error = close_error

    def close(self):
        self.close_count += 1
        if self.close_error is not None:
            raise self.close_error


def test_preview_reuses_0263_without_client_or_sql_read():
    store = FakeStore()
    calls = []

    def forbidden_builder(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("preview must not build binding")

    result = run_qdrant_controlled_scheduler_recall_binding(
        QdrantControlledSchedulerRecallCommand(
            embedding_report=_embedding_report(),
            store=store,
            configuration=_configuration(),
            execute=False,
        ),
        binding_builder=forbidden_builder,
    )

    assert result.valid is True
    assert calls == []
    assert store.calls == []
    assert result.dry_run is True
    assert result.binding_constructed is False
    assert result.qdrant_search_performed is False
    assert result.sql_rehydrate_attempted is False
    assert result.recall_request["query_ref"] == (
        "qdrant-query:e5-query:28"
    )
    assert result.usage_result["recall"]["planned"] is True


def test_execute_searches_refs_rehydrates_sql_and_closes():
    store = FakeStore()
    binding = FakeBinding()

    result = run_qdrant_controlled_scheduler_recall_binding(
        QdrantControlledSchedulerRecallCommand(
            embedding_report=_embedding_report(),
            store=store,
            configuration=_configuration(),
            limit=8,
            execute=True,
        ),
        binding_builder=lambda *args: binding,
    )

    assert result.valid is True
    assert binding.executor.search_count == 1
    assert binding.close_count == 1
    assert store.calls == [
        "sql:context:1",
        "sql:context:missing",
    ]
    assert result.binding_constructed is True
    assert result.binding_closed is True
    assert result.qdrant_search_performed is True
    assert result.sql_rehydrate_attempted is True
    assert result.usage_result["sql_refs"] == [
        "sql:context:1",
        "sql:context:missing",
    ]
    assert result.usage_result["hydrated_count"] == 1
    assert result.usage_result["missing_sql_refs"] == [
        "sql:context:missing"
    ]


def test_combined_binding_is_rejected_by_default():
    called = False

    def builder(*args, **kwargs):
        nonlocal called
        called = True
        return FakeBinding()

    result = run_qdrant_controlled_scheduler_recall_binding(
        QdrantControlledSchedulerRecallCommand(
            embedding_report=_embedding_report(),
            store=FakeStore(),
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
        "recall-only binding" in issue
        for issue in result.issues
    )


def test_limit_must_fit_configured_policy():
    result = run_qdrant_controlled_scheduler_recall_binding(
        QdrantControlledSchedulerRecallCommand(
            embedding_report=_embedding_report(),
            store=FakeStore(),
            configuration=_configuration(max_recall_hits=4),
            limit=8,
        )
    )

    assert result.valid is False
    assert (
        "recall limit exceeds configured max_recall_hits"
        in result.issues
    )


def test_invalid_embedding_is_reported_by_existing_0263():
    result = run_qdrant_controlled_scheduler_recall_binding(
        QdrantControlledSchedulerRecallCommand(
            embedding_report={"embedding": {}},
            store=FakeStore(),
            configuration=_configuration(),
        )
    )

    assert result.valid is False
    assert result.usage_result["valid"] is False
    assert "query vector must not be empty" in result.issues


def test_factory_error_is_serialized_without_search():
    report = QdrantScopedExecutorFactoryReport(
        valid=False,
        issues=("dependency invalid",),
        binding_ref="qdrant-real-binding:test",
        requested_operations=("recall",),
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

    result = run_qdrant_controlled_scheduler_recall_binding(
        QdrantControlledSchedulerRecallCommand(
            embedding_report=_embedding_report(),
            store=FakeStore(),
            configuration=_configuration(),
            execute=True,
        ),
        binding_builder=builder,
    )

    assert result.valid is False
    assert result.binding_constructed is False
    assert result.qdrant_search_performed is False
    assert result.sql_rehydrate_attempted is False
    assert result.factory_report["valid"] is False
    assert "dependency invalid" in result.issues


def test_close_failure_is_reported_after_successful_recall():
    binding = FakeBinding(
        close_error=RuntimeError("close refused")
    )

    result = run_qdrant_controlled_scheduler_recall_binding(
        QdrantControlledSchedulerRecallCommand(
            embedding_report=_embedding_report(),
            store=FakeStore(),
            configuration=_configuration(),
            execute=True,
        ),
        binding_builder=lambda *args: binding,
    )

    assert result.valid is False
    assert result.binding_constructed is True
    assert result.binding_closed is False
    assert result.qdrant_search_performed is True
    assert result.sql_rehydrate_attempted is True
    assert any(
        "scoped binding close failed" in issue
        for issue in result.issues
    )


def test_boundaries_preserve_current_architecture():
    result = run_qdrant_controlled_scheduler_recall_binding(
        QdrantControlledSchedulerRecallCommand(
            embedding_report=_embedding_report(),
            store=FakeStore(),
            configuration=_configuration(),
        )
    )

    assert dict(result.boundaries) == {
        "existing_0263_usage_reused": True,
        "existing_r3_factory_reused": True,
        "existing_sql_store_reused": True,
        "scheduler_owned_usage_preserved": True,
        "preview_constructs_client": False,
        "preview_reads_sql": False,
        "qdrant_search_requires_execute": True,
        "qdrant_returns_refs_only": True,
        "sql_remains_authority": True,
        "new_scheduler_added": False,
        "scheduler_run_modified": False,
        "new_qdrant_executor_added": False,
        "new_transport_added": False,
        "control_proxy_integrated": False,
        "event_bus_integrated": False,
        "shm_or_mmio_integrated": False,
        "qdrant_write_performed": False,
        "sql_write_performed": False,
        "projects_repository_change_required": False,
    }


def test_contracts_are_frozen():
    command = QdrantControlledSchedulerRecallCommand(
        embedding_report=_embedding_report(),
        store=FakeStore(),
        configuration=_configuration(),
    )
    policy = QdrantControlledSchedulerRecallPolicy()

    with pytest.raises(FrozenInstanceError):
        command.execute = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        policy.close_binding = False  # type: ignore[misc]
