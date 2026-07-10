from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from inference.qdrant_client_projection_executor import (
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
    QdrantClientExecutionError,
    QdrantClientProjectionExecutor,
    build_qdrant_client_projection_executor,
)
from inference.qdrant_projection_adapter import (
    QdrantProjectionPoint,
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
    QdrantRecallQuery,
)


@dataclass
class FakePointStruct:
    id: object
    vector: object
    payload: object


class FakeModels:
    PointStruct = FakePointStruct


class FakeClient:
    def __init__(self) -> None:
        self.upserts: list[dict[str, object]] = []
        self.queries: list[dict[str, object]] = []
        self.query_response = SimpleNamespace(points=[])
        self.closed = False

    def upsert(self, **kwargs):
        self.upserts.append(kwargs)
        return SimpleNamespace(status="completed")

    def query_points(self, **kwargs):
        self.queries.append(kwargs)
        return self.query_response

    def close(self) -> None:
        self.closed = True


def _target() -> QdrantProjectionTarget:
    return QdrantProjectionTarget(collection_name="autodoc_test", vector_dimension=2)


def _point() -> QdrantProjectionPoint:
    return QdrantProjectionPoint(
        point_id="qdrant-point:abc123",
        embedding_ref="embedding:passage:abc123",
        source_ref="ctx-fragment:sql:context:abc123",
        sql_context_ref="sql:context:abc123",
        vector=(1.0, 0.0),
        payload=(("role", "passage"),),
    )


def _executor(*, write: bool = True, search: bool = True) -> tuple[QdrantClientProjectionExecutor, FakeClient]:
    client = FakeClient()
    executor = QdrantClientProjectionExecutor(
        client=client,
        models_module=FakeModels,
        config=QdrantClientConnectionConfig(),
        gate=QdrantClientEffectGate(
            policy_decision_id="policy:0271:test",
            allow_write=write,
            allow_search=search,
        ),
    )
    return executor, client


def test_upsert_uses_uuid_storage_id_and_preserves_autodoc_refs() -> None:
    executor, client = _executor()

    result = executor.upsert_points((_point(),), target=_target(), policy=QdrantProjectionPolicy())

    assert result.acknowledged is True
    assert result.point_ids == ("qdrant-point:abc123",)
    request = client.upserts[0]
    stored = request["points"][0]
    assert stored.id != "qdrant-point:abc123"
    assert len(str(stored.id)) == 36
    assert stored.payload["autodoc_point_ref"] == "qdrant-point:abc123"
    assert stored.payload["sql_ref"] == "sql:context:abc123"
    assert stored.payload["sql_context_ref"] == "sql:context:abc123"
    assert request["wait"] is True


def test_search_returns_reference_only_hits_for_sql_rehydration() -> None:
    executor, client = _executor()
    client.query_response = SimpleNamespace(
        points=[
            SimpleNamespace(
                id="f4e1d074-67ab-4de0-8d92-358df819cad4",
                score=0.8,
                payload={
                    "autodoc_point_ref": "qdrant-point:abc123",
                    "sql_ref": "sql:context:abc123",
                    "source_ref": "ctx-fragment:sql:context:abc123",
                    "nested": {"not": "copied"},
                },
            )
        ]
    )

    result = executor.search_vector(
        (1.0, 0.0),
        target=_target(),
        policy=QdrantProjectionPolicy(max_recall_hits=4),
        query=QdrantRecallQuery(query_ref="qdrant-query:test", limit=4),
    )

    assert result.sql_context_refs == ("sql:context:abc123",)
    assert result.hits[0].point_id == "qdrant-point:abc123"
    assert result.hits[0].score == pytest.approx(0.9)
    assert "nested" not in dict(result.hits[0].payload)
    assert client.queries[0]["with_vectors"] is False


def test_gate_denies_effects_before_sdk_call() -> None:
    executor, client = _executor(write=False, search=False)

    with pytest.raises(QdrantClientExecutionError) as write_error:
        executor.upsert_points((_point(),), target=_target(), policy=QdrantProjectionPolicy())
    with pytest.raises(QdrantClientExecutionError) as search_error:
        executor.search_vector(
            (1.0, 0.0),
            target=_target(),
            policy=QdrantProjectionPolicy(),
            query=QdrantRecallQuery(query_ref="qdrant-query:test"),
        )

    assert write_error.value.failure.category == "gate_denied"
    assert search_error.value.failure.category == "gate_denied"
    assert client.upserts == []
    assert client.queries == []


def test_missing_sql_ref_fails_closed() -> None:
    executor, client = _executor()
    client.query_response = SimpleNamespace(
        points=[SimpleNamespace(id="deadbeef", score=0.5, payload={"source_ref": "ctx:test"})]
    )

    with pytest.raises(QdrantClientExecutionError) as error:
        executor.search_vector(
            (1.0, 0.0),
            target=_target(),
            policy=QdrantProjectionPolicy(),
            query=QdrantRecallQuery(query_ref="qdrant-query:test"),
        )

    assert error.value.failure.category == "missing_sql_ref"


def test_factory_injects_official_client_options_without_serializing_api_key() -> None:
    captured: dict[str, object] = {}

    def factory(**kwargs):
        captured.update(kwargs)
        return FakeClient()

    config = QdrantClientConnectionConfig(prefer_grpc=True, grpc_port=7334)
    executor = build_qdrant_client_projection_executor(
        config,
        QdrantClientEffectGate(policy_decision_id="policy:0271:test", allow_search=True),
        api_key="secret-value",
        client_factory=factory,
        models_module=FakeModels,
    )

    assert isinstance(executor, QdrantClientProjectionExecutor)
    assert captured["prefer_grpc"] is True
    assert captured["grpc_port"] == 7334
    assert captured["api_key"] == "secret-value"
    assert config.to_mapping()["api_key_serialized"] is False
    assert "secret-value" not in repr(config)


def test_sdk_error_is_wrapped_as_serializable_failure() -> None:
    class BrokenClient(FakeClient):
        def upsert(self, **kwargs):
            raise TimeoutError("backend timeout")

    executor = QdrantClientProjectionExecutor(
        client=BrokenClient(),
        models_module=FakeModels,
        config=QdrantClientConnectionConfig(),
        gate=QdrantClientEffectGate(policy_decision_id="policy:0271:test", allow_write=True),
    )

    with pytest.raises(QdrantClientExecutionError) as error:
        executor.upsert_points((_point(),), target=_target(), policy=QdrantProjectionPolicy())

    assert error.value.failure.to_mapping() == {
        "operation": "upsert",
        "category": "TimeoutError",
        "message": "backend timeout",
        "retryable": True,
    }


def test_close_delegates_without_starting_or_stopping_service() -> None:
    executor, client = _executor()
    executor.close()
    assert client.closed is True
