from types import SimpleNamespace

import pytest

from inference.qdrant_client_projection_executor import (
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
    QdrantClientExecutionError,
    QdrantClientProjectionExecutor,
)


class _Client:
    def __init__(self, records: list[object]) -> None:
        self.records = records
        self.calls: list[dict[str, object]] = []

    def retrieve(self, **kwargs: object) -> list[object]:
        self.calls.append(dict(kwargs))
        return self.records


class _Models:
    pass


def _record() -> object:
    return SimpleNamespace(
        id="uuid",
        payload={
            "point_id": "qdrant-point:test",
            "sql_ref": "sql:love-analysis:test",
            "source_ref": "sql:love-analysis:test",
            "source_content_digest": "sha256:" + "a" * 64,
            "context_revision_ref": "context-revision:test",
            "valid": True,
        },
    )


def _executor(client: _Client, *, allow_search: bool = True):
    return QdrantClientProjectionExecutor(
        client=client,
        models_module=_Models,
        config=QdrantClientConnectionConfig(),
        gate=QdrantClientEffectGate(
            policy_decision_id="policy:readback",
            allow_write=False,
            allow_search=allow_search,
        ),
    )


def test_exact_readback_uses_payload_only_and_disables_vectors() -> None:
    client = _Client([_record()])
    result = _executor(client).read_named_reference_point(
        collection_name="autodoc_context_e5_384_hybrid_v1",
        point_id="qdrant-point:test",
    )
    assert result is not None
    assert result.sql_ref == "sql:love-analysis:test"
    assert result.payload["source_content_digest"] == "sha256:" + "a" * 64
    assert client.calls[0]["with_payload"] is True
    assert client.calls[0]["with_vectors"] is False
    assert result.to_mapping()["boundaries"]["vectors_serialized"] is False


def test_missing_exact_point_returns_none() -> None:
    result = _executor(_Client([])).read_named_reference_point(
        collection_name="autodoc_context_e5_384_hybrid_v1",
        point_id="qdrant-point:missing",
    )
    assert result is None


def test_readback_gate_is_required() -> None:
    with pytest.raises(QdrantClientExecutionError) as captured:
        _executor(_Client([_record()]), allow_search=False).read_named_reference_point(
            collection_name="autodoc_context_e5_384_hybrid_v1",
            point_id="qdrant-point:test",
        )
    assert captured.value.failure.category == "gate_denied"
