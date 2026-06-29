from __future__ import annotations

import asyncio
from types import SimpleNamespace

from inference.e5_corpus import E5CorpusBuilder, E5CorpusDocument
from inference.e5_incremental import (
    E5IncrementalCorpusBuilder,
    embedding_matches_document,
    make_e5_document_hash,
)


class CountingPipeline:
    def __init__(self) -> None:
        self.seen: list[str] = []

    async def embed_text(self, text: str) -> object:
        self.seen.append(text)
        if "arnaque" in text:
            values = (1.0, 0.0)
        elif "moteur" in text:
            values = (0.0, 1.0)
        else:
            values = (0.5, 0.5)
        return SimpleNamespace(
            model="fake-e5",
            backend="fake-backend",
            tokenizer_name="fake-tokenizer",
            vector=SimpleNamespace(values=values, dimension=2, normalized=True, l2_norm=1.0),
        )


def test_incremental_builder_reuses_unchanged_embeddings() -> None:
    pipeline = CountingPipeline()
    previous = asyncio.run(E5CorpusBuilder(pipeline).build(["arnaque vendeur", "moteur diesel"]))
    assert pipeline.seen == ["passage: arnaque vendeur", "passage: moteur diesel"]
    pipeline.seen.clear()

    result = asyncio.run(
        E5IncrementalCorpusBuilder(pipeline).build(
            ["arnaque vendeur", "moteur diesel"],
            previous_index=previous,
            metadata={"source": "test"},
        )
    )

    assert pipeline.seen == []
    assert result.index.size == 2
    assert result.stats.reused_count == 2
    assert result.stats.embedded_count == 0
    assert result.stats.removed_count == 0
    assert result.index.metadata["incremental"] is True
    assert result.index.metadata["incremental_stats"]["reused_count"] == 2
    assert all(item.metadata["embedding_reused"] is True for item in result.index.embeddings)


def test_incremental_builder_embeds_only_changed_and_new_documents() -> None:
    pipeline = CountingPipeline()
    first = E5CorpusDocument.from_text("arnaque vendeur", id="stable-a")
    second = E5CorpusDocument.from_text("moteur diesel", id="stable-b")
    previous = asyncio.run(E5CorpusBuilder(pipeline).build([first, second]))
    pipeline.seen.clear()

    changed_second = E5CorpusDocument.from_text("moteur essence", id="stable-b")
    third = E5CorpusDocument.from_text("documentation OpenVINO", id="stable-c")
    result = asyncio.run(
        E5IncrementalCorpusBuilder(pipeline).build(
            [first, changed_second, third],
            previous_index=previous,
        )
    )

    assert pipeline.seen == ["passage: moteur essence", "passage: documentation OpenVINO"]
    assert result.stats.reused_count == 1
    assert result.stats.embedded_count == 2
    assert result.stats.removed_count == 0
    assert result.index.embeddings[0].metadata["embedding_reused"] is True
    assert result.index.embeddings[1].metadata["embedding_reused"] is False
    assert result.index.embeddings[2].metadata["embedding_reused"] is False


def test_incremental_builder_counts_removed_documents() -> None:
    pipeline = CountingPipeline()
    previous = asyncio.run(E5CorpusBuilder(pipeline).build(["arnaque vendeur", "moteur diesel", "autre doc"]))
    pipeline.seen.clear()

    result = asyncio.run(
        E5IncrementalCorpusBuilder(pipeline).build(
            ["arnaque vendeur"],
            previous_index=previous,
        )
    )

    assert pipeline.seen == []
    assert result.index.size == 1
    assert result.stats.reused_count == 1
    assert result.stats.embedded_count == 0
    assert result.stats.removed_count == 2


def test_document_hash_and_match_are_stable() -> None:
    document = E5CorpusDocument.from_text("arnaque vendeur", id="stable")
    same = E5CorpusDocument.from_text("arnaque vendeur", id="stable")
    changed = E5CorpusDocument.from_text("moteur diesel", id="stable")

    assert make_e5_document_hash(document) == make_e5_document_hash(same)
    assert make_e5_document_hash(document) != make_e5_document_hash(changed)

    index = asyncio.run(E5IncrementalCorpusBuilder(CountingPipeline()).build([document]))
    embedding = index.index.embeddings[0]
    assert embedding_matches_document(embedding, same)
    assert not embedding_matches_document(embedding, changed)
