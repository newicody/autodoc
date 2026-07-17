from types import SimpleNamespace

import pytest

from inference.qdrant_client_projection_executor import (
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
    QdrantClientExecutionError,
    QdrantClientProjectionExecutor,
)


class _PointStruct:
    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


class _SparseVector:
    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


class _Client:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def upsert(self, **kwargs: object) -> object:
        self.calls.append(dict(kwargs))
        return SimpleNamespace(status="completed")


def _payload() -> dict[str, object]:
    return {
        "point_id": "qdrant-point:test",
        "sql_ref": "sql:analysis:test",
        "source_ref": "sql:analysis:test",
        "source_content_digest": "sha256:" + "a" * 64,
        "context_revision_ref": "context-revision:test",
        "branch_ref": "branch:main",
        "project_ref": "project:test",
        "conversation_ref": "conversation:test",
        "artifact_kind": "specialist_analysis",
        "contribution_kind": "concept_affect_analysis",
        "specialist_ref": "specialist:test",
        "laboratory_ref": "laboratory:test",
        "security_scope": "security-scope:test",
        "valid": True,
        "superseded_by": "",
    }


def _executor(*, allow_write: bool = True) -> tuple[QdrantClientProjectionExecutor, _Client]:
    client = _Client()
    models = SimpleNamespace(PointStruct=_PointStruct, SparseVector=_SparseVector)
    executor = QdrantClientProjectionExecutor(
        client=client,
        models_module=models,
        config=QdrantClientConnectionConfig(),
        gate=QdrantClientEffectGate(
            policy_decision_id="policy:r11-test",
            allow_write=allow_write,
        ),
    )
    return executor, client


def test_upserts_one_named_dense_sparse_point_without_content() -> None:
    executor, client = _executor()
    result = executor.upsert_named_hybrid_point(
        collection_name="autodoc_context_e5_384_hybrid_v1",
        point_id="qdrant-point:test",
        dense_vector_name="dense_e5_v1",
        dense_values=(1.0,) + (0.0,) * 383,
        sparse_vector_name="sparse_lexical_v1",
        sparse_indices=(7, 11),
        sparse_values=(0.6, 0.8),
        payload=_payload(),
    )

    assert result.acknowledged is True
    assert result.to_mapping()["boundaries"]["vectors_serialized"] is False
    call = client.calls[0]
    point = call["points"][0]
    assert tuple(point.vector) == ("dense_e5_v1", "sparse_lexical_v1")
    assert point.vector["dense_e5_v1"] == [1.0] + [0.0] * 383
    assert point.vector["sparse_lexical_v1"].indices == [7, 11]
    assert "body" not in point.payload
    assert "content" not in point.payload


def test_named_hybrid_upsert_requires_explicit_write_gate() -> None:
    executor, client = _executor(allow_write=False)
    with pytest.raises(QdrantClientExecutionError, match="gate_denied"):
        executor.upsert_named_hybrid_point(
            collection_name="autodoc_context_e5_384_hybrid_v1",
            point_id="qdrant-point:test",
            dense_vector_name="dense_e5_v1",
            dense_values=(1.0,) + (0.0,) * 383,
            sparse_vector_name="sparse_lexical_v1",
            sparse_indices=(7,),
            sparse_values=(1.0,),
            payload=_payload(),
        )
    assert client.calls == []


def test_named_hybrid_upsert_rejects_authoritative_body() -> None:
    executor, client = _executor()
    payload = _payload()
    payload["body"] = "must remain in SQL"
    with pytest.raises(QdrantClientExecutionError, match="forbidden_payload"):
        executor.upsert_named_hybrid_point(
            collection_name="autodoc_context_e5_384_hybrid_v1",
            point_id="qdrant-point:test",
            dense_vector_name="dense_e5_v1",
            dense_values=(1.0,) + (0.0,) * 383,
            sparse_vector_name="sparse_lexical_v1",
            sparse_indices=(7,),
            sparse_values=(1.0,),
            payload=payload,
        )
    assert client.calls == []
