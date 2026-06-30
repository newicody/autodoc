from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from inference.e5_corpus import E5CorpusEmbedding, E5CorpusIndex
from inference.e5_search_validation import E5SearchValidationQueryResult, validate_e5_search_queries


class FakePipeline:
    async def embed_text(self, text: str) -> object:
        values = (1.0, 0.0) if "alpha" in text else (0.0, 1.0)
        return SimpleNamespace(
            model="fake-e5",
            backend="fake-backend",
            tokenizer_name="fake-tokenizer",
            vector=SimpleNamespace(values=values, dimension=2, normalized=True, l2_norm=1.0),
        )


def _index() -> E5CorpusIndex:
    return E5CorpusIndex(
        model="fake-e5",
        backend="fake-backend",
        tokenizer="fake-tokenizer",
        dimension=2,
        embeddings=(
            E5CorpusEmbedding(
                id="alpha",
                text="alpha document",
                prefixed_text="passage: alpha document",
                vector=(1.0, 0.0),
                dimension=2,
                normalized=True,
                l2_norm=1.0,
                metadata={"source_path": "alpha.md", "source_extension": ".md"},
            ),
            E5CorpusEmbedding(
                id="beta",
                text="beta document",
                prefixed_text="passage: beta document",
                vector=(0.0, 1.0),
                dimension=2,
                normalized=True,
                l2_norm=1.0,
                metadata={"source_path": "beta.md", "source_extension": ".md"},
            ),
        ),
    )


def _alpha_only_index() -> E5CorpusIndex:
    return E5CorpusIndex(
        model="fake-e5",
        backend="fake-backend",
        tokenizer="fake-tokenizer",
        dimension=2,
        embeddings=(
            E5CorpusEmbedding(
                id="alpha",
                text="alpha document",
                prefixed_text="passage: alpha document",
                vector=(1.0, 0.0),
                dimension=2,
                normalized=True,
                l2_norm=1.0,
                metadata={"source_path": "alpha.md", "source_extension": ".md"},
            ),
        ),
    )


def test_validate_e5_search_queries_reports_each_query() -> None:
    results = asyncio.run(
        validate_e5_search_queries(
            FakePipeline(),
            _index(),
            ("alpha", "beta"),
            limit=1,
            min_score=0.5,
        )
    )

    assert [item.query for item in results] == ["alpha", "beta"]
    assert [item.hit_count for item in results] == [1, 1]
    assert all(item.passed for item in results)
    assert results[0].best_score == 1.0
    assert results[0].min_score == 0.5


def test_validate_e5_search_queries_reports_failed_query_after_min_score() -> None:
    results = asyncio.run(
        validate_e5_search_queries(
            FakePipeline(),
            _alpha_only_index(),
            ("beta",),
            limit=1,
            min_score=0.5,
        )
    )

    assert results[0].hit_count == 0
    assert results[0].passed is False


def test_search_validation_query_result_json_is_stable() -> None:
    result = E5SearchValidationQueryResult(
        query="alpha",
        hit_count=1,
        best_score=0.9,
        min_score=0.8,
    )

    assert result.to_json_dict() == {
        "query": "alpha",
        "hit_count": 1,
        "best_score": 0.9,
        "min_score": 0.8,
        "passed": True,
    }
    assert "best_score: 0.90000000" in "\n".join(result.to_text_lines())


def test_validate_e5_search_queries_rejects_invalid_options() -> None:
    with pytest.raises(ValueError, match="limit"):
        asyncio.run(validate_e5_search_queries(FakePipeline(), _index(), ("alpha",), limit=0))
    with pytest.raises(ValueError, match="min_score"):
        asyncio.run(validate_e5_search_queries(FakePipeline(), _index(), ("alpha",), min_score=1.1))
