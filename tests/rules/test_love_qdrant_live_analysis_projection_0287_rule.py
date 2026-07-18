from __future__ import annotations

from types import SimpleNamespace

import context.love_qdrant_live_analysis_projection_0287 as module


def test_projection_port_delegates_reference_only_readback(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        module,
        "AsyncEmbeddingPipeline",
        object,
    )
    monkeypatch.setattr(
        module,
        "NamedHybridProjectionWriter",
        object,
    )

    observed: list[tuple[str, str]] = []
    writer = SimpleNamespace(
        read_named_reference_point=lambda **kwargs: (
            observed.append(
                (
                    kwargs["collection_name"],
                    kwargs["point_id"],
                )
            )
            or SimpleNamespace(payload={"sql_ref": "context-object:test"})
        ),
        upsert_named_hybrid_point=lambda **kwargs: None,
    )
    port = module.LoveQdrantLiveAnalysisProjection(
        pipeline=object(),
        writer=writer,
    )

    result = port.read_named_reference_point(
        collection_name="autodoc_context_e5_384_hybrid_v1",
        point_id="qdrant-point:test",
    )

    assert observed == [
        (
            "autodoc_context_e5_384_hybrid_v1",
            "qdrant-point:test",
        )
    ]
    assert result.payload["sql_ref"] == "context-object:test"
