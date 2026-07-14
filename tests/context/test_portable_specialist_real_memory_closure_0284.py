from __future__ import annotations

from types import SimpleNamespace

from context.portable_specialist_real_memory_closure_0284 import (
    EXPECTED_E5_DIMENSION,
    _real_embedding_issues,
    verify_portable_specialist_real_memory_result,
)


def _embedding(role: str) -> dict[str, object]:
    vector = [0.0] * EXPECTED_E5_DIMENSION
    vector[0] = 1.0
    return {
        "embedding_ref": f"embedding:{role}:0284-r6",
        "role": role,
        "dimension": EXPECTED_E5_DIMENSION,
        "normalized": True,
        "vector": vector,
        "metadata": {
            "model": "openvino.embedding.e5-small",
            "model_path": "/models/multilingual-e5-small/openvino_model.xml",
        },
    }


def _specialist_result() -> SimpleNamespace:
    sql_ref = "sql:specialist-output:0284-r6"
    existing = SimpleNamespace(
        sql_ref=sql_ref,
        handoff={
            "sql_write_performed": True,
            "sql_readback_performed": True,
            "openvino_call_performed": True,
            "qdrant_write_performed": True,
            "embedding": {"embedding": _embedding("passage")},
            "projection": {
                "valid": True,
                "execute": True,
                "dry_run": False,
                "write_result": {
                    "acknowledged": True,
                    "point_ids": ["qdrant-point:0284-r6"],
                }
            },
        },
        recall={
            "query_openvino_call_performed": True,
            "qdrant_recall_performed": True,
            "sql_rehydrate_performed": True,
            "query_embedding": {"embedding": _embedding("query")},
            "recall_rehydrate": {
                "valid": True,
                "execute": True,
                "dry_run": False,
                "qdrant_recall_refs_only": True,
                "sql_remains_authority": True,
                "sql_refs": [sql_ref],
                "hydrated_records": [{"context_ref": sql_ref}],
            },
        },
    )
    return SimpleNamespace(
        valid=True,
        existing_smoke=existing,
        portable_identity_preserved=True,
        message_contract_closed=True,
    )


def test_real_memory_verifier_closes_the_existing_path() -> None:
    result = verify_portable_specialist_real_memory_result(
        _specialist_result(),
        embedding_runtime_injected=False,
    )

    assert result["issues"] == ()
    assert result["memory_closed"] is True
    assert result["real_sql_authority_used"] is True
    assert result["real_openvino_e5_used"] is True
    assert result["real_qdrant_projection_used"] is True
    assert result["real_qdrant_recall_used"] is True
    assert result["qdrant_returns_references_only"] is True
    assert result["sql_rehydration_verified"] is True
    assert result["returned_sql_refs"] == (
        "sql:specialist-output:0284-r6",
    )


def test_injected_embedding_runtime_cannot_prove_live_openvino() -> None:
    result = verify_portable_specialist_real_memory_result(
        _specialist_result(),
        embedding_runtime_injected=True,
    )

    assert result["memory_closed"] is False
    assert result["real_openvino_e5_used"] is False
    assert any("injected embedding runtime" in issue for issue in result["issues"])


def test_embedding_verifier_rejects_dimension_385() -> None:
    embedding = _embedding("passage")
    embedding["dimension"] = 385
    embedding["vector"] = [0.0] * 385

    issues = _real_embedding_issues(embedding, role="passage")

    assert "passage embedding dimension must be 384" in issues
    assert "passage vector length must be 384" in issues


def test_verifier_rejects_recall_without_reference_only_boundary() -> None:
    specialist = _specialist_result()
    specialist.existing_smoke.recall["recall_rehydrate"][
        "qdrant_recall_refs_only"
    ] = False

    result = verify_portable_specialist_real_memory_result(
        specialist,
        embedding_runtime_injected=False,
    )

    assert result["memory_closed"] is False
    assert result["qdrant_returns_references_only"] is False
    assert "Qdrant recall must return references only" in result["issues"]
