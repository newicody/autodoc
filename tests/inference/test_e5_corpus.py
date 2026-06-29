from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from inference.e5_corpus import (
    E5CorpusBuilder,
    E5CorpusDocument,
    E5CorpusEmbedding,
    E5CorpusIndex,
    E5CorpusJsonStore,
    E5CorpusSearcher,
    make_corpus_document_id,
)
from inference.e5_text import E5Text


class FakePipeline:
    def __init__(self) -> None:
        self.seen: list[str] = []

    async def embed_text(self, text: str) -> object:
        self.seen.append(text)
        if text.startswith("query:") and ("arnaque" in text or "baiser" in text):
            values = (1.0, 0.0, 0.0)
        elif "arnaque" in text or "tromperie" in text:
            values = (1.0, 0.0, 0.0)
        elif "moteur" in text:
            values = (0.0, 1.0, 0.0)
        else:
            values = (0.0, 0.0, 1.0)
        return SimpleNamespace(
            model="fake-e5",
            backend="fake-backend",
            tokenizer_name="fake-tokenizer",
            vector=SimpleNamespace(values=values, dimension=len(values), normalized=True, l2_norm=1.0),
        )


def test_make_corpus_document_id_is_stable_and_indexed() -> None:
    assert make_corpus_document_id("passage: test", index=1).startswith("doc-000001-")
    assert make_corpus_document_id("passage: test") == make_corpus_document_id("passage: test")
    with pytest.raises(ValueError, match="positive"):
        make_corpus_document_id("passage: test", index=0)


def test_corpus_document_forces_passage_role() -> None:
    doc = E5CorpusDocument.from_text("arnaque vendeur", index=1)

    assert doc.text.prefixed == "passage: arnaque vendeur"

    with pytest.raises(ValueError, match="passage"):
        E5CorpusDocument.from_text(E5Text.query("mauvais"), index=1)


def test_corpus_builder_embeds_passages_once() -> None:
    pipeline = FakePipeline()
    builder = E5CorpusBuilder(pipeline)
    index = asyncio.run(builder.build(["arnaque vendeur", "problème moteur"], metadata={"source": "test"}))

    assert index.size == 2
    assert index.model == "fake-e5"
    assert index.backend == "fake-backend"
    assert index.tokenizer == "fake-tokenizer"
    assert index.dimension == 3
    assert index.metadata["source"] == "test"
    assert pipeline.seen == ["passage: arnaque vendeur", "passage: problème moteur"]


def test_corpus_searcher_reuses_persisted_passage_embeddings() -> None:
    pipeline = FakePipeline()
    index = asyncio.run(E5CorpusBuilder(pipeline).build(["problème moteur", "arnaque vendeur", "autre doc"]))

    pipeline.seen.clear()
    results = asyncio.run(E5CorpusSearcher(pipeline).search("je me suis fait baiser", index, limit=2))

    assert pipeline.seen == ["query: je me suis fait baiser"]
    assert len(results.hits) == 2
    assert results.best is not None
    assert results.best.text == "arnaque vendeur"
    assert results.best.score == 1.0


def test_corpus_searcher_filters_hits_below_min_score() -> None:
    pipeline = FakePipeline()
    index = asyncio.run(E5CorpusBuilder(pipeline).build(["problème moteur", "arnaque vendeur", "autre doc"]))

    results = asyncio.run(
        E5CorpusSearcher(pipeline).search(
            "je me suis fait baiser",
            index,
            min_score=0.5,
        )
    )

    assert [hit.text for hit in results.hits] == ["arnaque vendeur"]
    assert results.hits[0].rank == 1
    assert results.hits[0].score == 1.0


def test_corpus_searcher_keeps_hit_equal_to_min_score() -> None:
    pipeline = FakePipeline()
    index = asyncio.run(E5CorpusBuilder(pipeline).build(["arnaque vendeur", "moteur diesel"]))

    results = asyncio.run(
        E5CorpusSearcher(pipeline).search(
            "je me suis fait baiser",
            index,
            min_score=1.0,
        )
    )

    assert [hit.text for hit in results.hits] == ["arnaque vendeur"]


def test_corpus_searcher_returns_empty_hits_when_min_score_filters_everything() -> None:
    pipeline = FakePipeline()
    index = asyncio.run(E5CorpusBuilder(pipeline).build(["moteur diesel", "autre doc"]))

    results = asyncio.run(
        E5CorpusSearcher(pipeline).search(
            "je me suis fait baiser",
            index,
            min_score=0.5,
        )
    )

    assert results.hits == ()
    assert results.best is None


def test_corpus_searcher_rejects_wrong_role_invalid_limit_and_invalid_min_score() -> None:
    pipeline = FakePipeline()
    index = asyncio.run(E5CorpusBuilder(pipeline).build(["passage OK"]))
    searcher = E5CorpusSearcher(pipeline)

    with pytest.raises(ValueError, match="query"):
        asyncio.run(searcher.search(E5Text.passage("document"), index))

    with pytest.raises(ValueError, match="limit"):
        asyncio.run(searcher.search("question", index, limit=0))

    with pytest.raises(ValueError, match="min_score"):
        asyncio.run(searcher.search("question", index, min_score=1.1))


def test_corpus_json_store_roundtrip(tmp_path) -> None:
    index = asyncio.run(E5CorpusBuilder(FakePipeline()).build(["arnaque vendeur", "moteur diesel"]))

    store = E5CorpusJsonStore()
    path = tmp_path / "corpus.json"
    written = store.write(index, path)

    loaded = store.read(written)

    assert loaded.to_json_dict() == index.to_json_dict()

    with pytest.raises(FileExistsError):
        store.write(index, path)

    store.write(index, path, overwrite=True)


def test_corpus_json_store_rejects_missing_parent(tmp_path) -> None:
    index = asyncio.run(E5CorpusBuilder(FakePipeline()).build(["arnaque vendeur"]))

    with pytest.raises(FileNotFoundError):
        E5CorpusJsonStore().write(index, tmp_path / "missing" / "corpus.json")


def test_corpus_index_validates_unique_ids_and_dimensions() -> None:
    first = E5CorpusEmbedding(
        id="same",
        text="a",
        prefixed_text="passage: a",
        vector=(1.0, 0.0),
        dimension=2,
        normalized=True,
        l2_norm=1.0,
    )
    second = E5CorpusEmbedding(
        id="same",
        text="b",
        prefixed_text="passage: b",
        vector=(0.0, 1.0),
        dimension=2,
        normalized=True,
        l2_norm=1.0,
    )

    with pytest.raises(ValueError, match="unique"):
        E5CorpusIndex(
            model="m",
            backend="b",
            tokenizer="t",
            dimension=2,
            embeddings=(first, second),
        )


def test_corpus_json_store_atomic_roundtrip_and_overwrite(tmp_path) -> None:
    index = asyncio.run(E5CorpusBuilder(FakePipeline()).build(["arnaque vendeur"]))
    store = E5CorpusJsonStore()
    path = tmp_path / "corpus.json"

    written = store.write_atomic(index, path)

    assert written == path
    assert store.read(path).to_json_dict() == index.to_json_dict()
    assert not (tmp_path / ".corpus.json.tmp").exists()

    with pytest.raises(FileExistsError):
        store.write_atomic(index, path)

    store.write_atomic(index, path, overwrite=True)


def test_corpus_json_store_atomic_does_not_replace_existing_when_validation_fails(tmp_path) -> None:
    index = asyncio.run(E5CorpusBuilder(FakePipeline()).build(["arnaque vendeur"]))
    path = tmp_path / "corpus.json"
    path.write_text("old corpus\n", encoding="utf-8")

    class BrokenValidationStore(E5CorpusJsonStore):
        def read(self, path):  # type: ignore[no-untyped-def]
            raise ValueError("forced validation failure")

    with pytest.raises(ValueError, match="forced validation failure"):
        BrokenValidationStore().write_atomic(index, path, overwrite=True)

    assert path.read_text(encoding="utf-8") == "old corpus\n"
    assert not (tmp_path / ".corpus.json.tmp").exists()
