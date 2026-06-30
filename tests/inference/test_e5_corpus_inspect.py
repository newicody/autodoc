from __future__ import annotations

import pytest

from inference.e5_corpus import E5CorpusEmbedding, E5CorpusIndex
from inference.e5_corpus_inspect import inspect_e5_corpus


def _embedding(
    id: str,
    source_path: str | None,
    *,
    source_extension: str | None = ".md",
    embedding_reused: bool | None = None,
) -> E5CorpusEmbedding:
    metadata: dict[str, object] = {}
    if source_path is not None:
        metadata["source_path"] = source_path
    if source_extension is not None:
        metadata["source_extension"] = source_extension
    if embedding_reused is not None:
        metadata["embedding_reused"] = embedding_reused
    return E5CorpusEmbedding(
        id=id,
        text=f"text {id}",
        prefixed_text=f"passage: text {id}",
        vector=(1.0, 0.0),
        dimension=2,
        normalized=True,
        l2_norm=1.0,
        metadata=metadata,
    )


def _index() -> E5CorpusIndex:
    return E5CorpusIndex(
        model="openvino.embedding.e5-small",
        backend="openvino.embedding.e5-small",
        tokenizer="transformers.multilingual-e5-small",
        dimension=2,
        embeddings=(
            _embedding("a", "README.md", embedding_reused=True),
            _embedding("b", "README.md", embedding_reused=False),
            _embedding("c", "doc/ARCHITECTURE_LAYERS.md", embedding_reused=False),
            _embedding("d", None, source_extension=None),
        ),
    )


def test_inspect_e5_corpus_counts_sources_extensions_and_reuse() -> None:
    diagnostics = inspect_e5_corpus(_index())

    assert diagnostics.schema == "missipy.e5.corpus.v1"
    assert diagnostics.chunk_count == 4
    assert diagnostics.source_count == 2
    assert diagnostics.extension_counts == {".md": 3, "unknown": 1}
    assert diagnostics.embedding_reused_count == 1
    assert diagnostics.embedding_embedded_count == 2
    assert diagnostics.embedding_reuse_unknown_count == 1
    assert diagnostics.missing_source_count == 1
    assert diagnostics.has_warnings is True


def test_inspect_e5_corpus_reports_top_sources_in_stable_order() -> None:
    diagnostics = inspect_e5_corpus(_index(), top_sources_limit=2)

    assert [item.source_path for item in diagnostics.top_sources] == [
        "README.md",
        "doc/ARCHITECTURE_LAYERS.md",
    ]
    assert [item.chunk_count for item in diagnostics.top_sources] == [2, 1]


def test_inspect_e5_corpus_text_output_is_stable() -> None:
    text = inspect_e5_corpus(_index(), top_sources_limit=1).to_text()

    assert "model: openvino.embedding.e5-small" in text
    assert "chunk_count: 4" in text
    assert "extensions:" in text
    assert "  .md: 3" in text
    assert "top_sources:" in text
    assert "  README.md: 2 (.md)" in text
    assert "missing_source_path: 1" in text


def test_inspect_e5_corpus_rejects_invalid_top_sources_limit() -> None:
    with pytest.raises(ValueError, match="top_sources_limit"):
        inspect_e5_corpus(_index(), top_sources_limit=0)
