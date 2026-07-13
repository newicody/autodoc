from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from inference.qdrant_client_projection_executor import (
    QdrantClientConnectionConfig,
    QdrantClientDependencyReadiness,
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
from inference.qdrant_real_binding_readiness_0283 import (
    QdrantRealBindingReadinessCommand,
    QdrantRealBindingReadinessPolicy,
    inspect_qdrant_real_binding_readiness,
)
from inference.qdrant_sql_authority_scope import (
    QdrantSqlAuthorityScope,
    QdrantStrictGrpcTransportPolicy,
)


def _dependency():
    return QdrantClientDependencyReadiness(
        installed=True,
        version="1.18.0",
    )


def _configuration(
    *,
    operations=("projection", "recall"),
    dimension=384,
    distance="Cosine",
    api_key_env_var="",
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
                policy_decision_id="policy:0283:r6",
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
                vector_dimension=dimension,
                distance=distance,
            ),
            projection_policy=QdrantProjectionPolicy(),
            requested_operations=operations,
            api_key_env_var=api_key_env_var,
        )
    )


def _collection_info(
    *,
    status="green",
    dimension=384,
    distance="Cosine",
):
    return SimpleNamespace(
        status=status,
        config=SimpleNamespace(
            params=SimpleNamespace(
                vectors=SimpleNamespace(
                    size=dimension,
                    distance=distance,
                )
            )
        ),
    )


class FakeClient:
    def __init__(self, info=None, error=None):
        self.info = info
        self.error = error
        self.get_count = 0
        self.close_count = 0

    def get_collection(self, collection_name):
        self.get_count += 1
        if self.error is not None:
            raise self.error
        return self.info

    def close(self):
        self.close_count += 1


def test_local_readiness_does_not_construct_client():
    calls = []

    def forbidden_builder(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("local readiness must not build client")

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(),
            live_probe=False,
        ),
        dependency_inspector=_dependency,
        client_builder=forbidden_builder,
    )

    assert result.valid is True
    assert result.local_ready is True
    assert result.operational_ready is False
    assert result.projection_ready is False
    assert result.recall_ready is False
    assert result.live_probe_requested is False
    assert result.live_probe_performed is False
    assert result.client_constructed is False
    assert calls == []
    assert "live collection probe not requested" in result.warnings


def test_live_probe_reads_compatible_collection_and_closes():
    client = FakeClient(info=_collection_info())

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(),
            live_probe=True,
        ),
        dependency_inspector=_dependency,
        client_builder=lambda *args, **kwargs: client,
    )

    assert result.valid is True
    assert result.local_ready is True
    assert result.operational_ready is True
    assert result.projection_ready is True
    assert result.recall_ready is True
    assert result.live_probe_performed is True
    assert result.client_constructed is True
    assert result.client_closed is True
    assert result.collection_read_performed is True
    assert client.get_count == 1
    assert client.close_count == 1
    assert result.collection_report["status"] == "Green"
    assert result.collection_report["vector_dimension"] == 384
    assert result.collection_report["distance"] == "Cosine"
    assert result.collection_report["compatible"] is True


def test_projection_only_readiness_does_not_claim_recall_ready():
    client = FakeClient(info=_collection_info())

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(
                operations=("projection",)
            ),
            live_probe=True,
        ),
        dependency_inspector=_dependency,
        client_builder=lambda *args, **kwargs: client,
    )

    assert result.operational_ready is True
    assert result.projection_ready is True
    assert result.recall_ready is False


def test_recall_only_readiness_does_not_claim_projection_ready():
    client = FakeClient(info=_collection_info(status="yellow"))

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(
                operations=("recall",)
            ),
            live_probe=True,
        ),
        dependency_inspector=_dependency,
        client_builder=lambda *args, **kwargs: client,
    )

    assert result.operational_ready is True
    assert result.projection_ready is False
    assert result.recall_ready is True
    assert result.collection_report["status"] == "Yellow"


def test_dimension_mismatch_blocks_operational_readiness():
    client = FakeClient(
        info=_collection_info(dimension=768)
    )

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(),
            live_probe=True,
        ),
        dependency_inspector=_dependency,
        client_builder=lambda *args, **kwargs: client,
    )

    assert result.valid is False
    assert result.operational_ready is False
    assert result.collection_report["dimension_matches"] is False
    assert any(
        "expected 384, got 768" in issue
        for issue in result.issues
    )


def test_distance_mismatch_blocks_operational_readiness():
    client = FakeClient(
        info=_collection_info(distance="Dot")
    )

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(),
            live_probe=True,
        ),
        dependency_inspector=_dependency,
        client_builder=lambda *args, **kwargs: client,
    )

    assert result.valid is False
    assert result.operational_ready is False
    assert result.collection_report["distance_matches"] is False


def test_red_collection_status_is_not_ready():
    client = FakeClient(
        info=_collection_info(status="red")
    )

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(),
            live_probe=True,
        ),
        dependency_inspector=_dependency,
        client_builder=lambda *args, **kwargs: client,
    )

    assert result.valid is False
    assert result.operational_ready is False
    assert "collection status is not allowed: Red" in result.issues


def test_named_vector_collection_is_rejected_for_unnamed_target():
    info = SimpleNamespace(
        status="green",
        config=SimpleNamespace(
            params=SimpleNamespace(
                vectors={
                    "title": {
                        "size": 384,
                        "distance": "Cosine",
                    }
                }
            )
        ),
    )
    client = FakeClient(info=info)

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(),
            live_probe=True,
        ),
        dependency_inspector=_dependency,
        client_builder=lambda *args, **kwargs: client,
    )

    assert result.valid is False
    assert result.collection_report["vector_shape"] == (
        "named-vectors-unsupported"
    )
    assert (
        "collection vector dimension is unavailable"
        in result.issues
    )


def test_dependency_failure_skips_live_probe():
    calls = []

    def builder(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeClient(info=_collection_info())

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(),
            live_probe=True,
        ),
        dependency_inspector=lambda: (
            QdrantClientDependencyReadiness(
                installed=False,
                version="",
            )
        ),
        client_builder=builder,
    )

    assert result.valid is False
    assert result.local_ready is False
    assert result.live_probe_performed is False
    assert result.client_constructed is False
    assert calls == []
    assert any(
        issue.startswith("factory:")
        for issue in result.issues
    )


def test_missing_remote_secret_skips_live_probe():
    configuration = build_qdrant_real_binding_configuration(
        QdrantRealBindingConfigurationCommand(
            connection=QdrantClientConnectionConfig(
                url="https://qdrant.example.invalid",
                timeout_seconds=10.0,
                prefer_grpc=True,
                grpc_port=6334,
                wait_for_write=True,
                check_compatibility=True,
            ),
            effect_gate=QdrantClientEffectGate(
                policy_decision_id="policy:0283:r6:remote",
                allow_search=True,
            ),
            sql_authority_scope=QdrantSqlAuthorityScope(
                authority_ref="sql-authority:postgres:fixture",
                store_kind="postgresql",
            ),
            transport_policy=QdrantStrictGrpcTransportPolicy(
                rest_admin_url="https://qdrant.example.invalid",
                grpc_port=6334,
            ),
            target=QdrantProjectionTarget(
                collection_name="autodoc_context_embeddings",
                vector_dimension=384,
            ),
            projection_policy=QdrantProjectionPolicy(),
            requested_operations=("recall",),
            api_key_env_var="QDRANT_API_KEY",
        ),
        policy=__import__(
            "inference.qdrant_real_binding_configuration_0283",
            fromlist=["QdrantRealBindingConfigurationPolicy"],
        ).QdrantRealBindingConfigurationPolicy(
            require_loopback=False,
        ),
    )
    calls = []

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=configuration,
            live_probe=True,
        ),
        dependency_inspector=_dependency,
        environment={},
        client_builder=lambda *args, **kwargs: calls.append(1),
    )

    assert result.valid is False
    assert calls == []
    assert any(
        "environment variable is missing or empty" in issue
        for issue in result.issues
    )


def test_probe_failure_is_serialized_and_client_is_closed():
    client = FakeClient(
        error=RuntimeError("service unavailable")
    )

    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(),
            live_probe=True,
        ),
        dependency_inspector=_dependency,
        client_builder=lambda *args, **kwargs: client,
    )

    assert result.valid is False
    assert result.client_constructed is True
    assert result.client_closed is True
    assert result.collection_read_performed is False
    assert client.close_count == 1
    assert any(
        "service unavailable" in issue
        for issue in result.issues
    )


def test_boundaries_preserve_current_architecture():
    result = inspect_qdrant_real_binding_readiness(
        QdrantRealBindingReadinessCommand(
            configuration=_configuration(),
        ),
        dependency_inspector=_dependency,
    )

    assert dict(result.boundaries) == {
        "existing_r2_configuration_reused": True,
        "existing_r3_factory_inspection_reused": True,
        "existing_dependency_inspection_reused": True,
        "live_probe_is_explicit": True,
        "live_probe_read_only": True,
        "collection_created": False,
        "collection_updated": False,
        "collection_deleted": False,
        "qdrant_write_performed": False,
        "qdrant_search_performed": False,
        "sql_read_performed": False,
        "sql_write_performed": False,
        "qdrant_started": False,
        "new_scheduler_added": False,
        "scheduler_run_modified": False,
        "new_qdrant_executor_added": False,
        "new_transport_added": False,
        "control_proxy_integrated": False,
        "event_bus_integrated": False,
        "shm_or_mmio_integrated": False,
        "projects_repository_change_required": False,
    }


def test_contracts_are_frozen():
    command = QdrantRealBindingReadinessCommand(
        configuration=_configuration(),
    )
    policy = QdrantRealBindingReadinessPolicy()

    with pytest.raises(FrozenInstanceError):
        command.live_probe = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        policy.close_client = False  # type: ignore[misc]
