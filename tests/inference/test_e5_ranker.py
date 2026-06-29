from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from inference.e5_ranker import E5LocalRanker, dot_product
from inference.e5_text import E5Text


class FakePipeline:
    def __init__(self) -> None:
        self.seen: list[str] = []

    async def embed_text(self, text: str) -> object:
        self.seen.append(text)
        if "arnaque" in text or "baiser" in text:
            values = (1.0, 0.0, 0.0)
        elif "moteur" in text:
            values = (0.0, 1.0, 0.0)
        else:
            values = (0.0, 0.0, 1.0)
        return SimpleNamespace(
            text=text,
            model="fake-e5",
            backend="fake-e5",
            tokenizer_name="fake-tokenizer",
            vector=SimpleNamespace(values=values, dimension=len(values), normalized=True, l2_norm=1.0),
        )


def test_dot_product_requires_same_dimension() -> None:
    assert dot_product((1.0, 2.0), (3.0, 4.0)) == 11.0
    with pytest.raises(ValueError, match="same dimension"):
        dot_product((1.0,), (1.0, 2.0))


def test_e5_ranker_prefixes_query_and_passages() -> None:
    pipeline = FakePipeline()
    ranker = E5LocalRanker(pipeline)

    result = asyncio.run(
        ranker.rank(
            "je me suis fait baiser",
            [
                "problème moteur diesel",
                "passage: arnaque vendeur voiture",
                "documentation OpenVINO",
            ],
        )
    )

    assert result.query.prefixed == "query: je me suis fait baiser"
    assert result.best is not None
    assert result.best.passage.prefixed == "passage: arnaque vendeur voiture"
    assert result.best.score == 1.0
    assert pipeline.seen == [
        "query: je me suis fait baiser",
        "passage: problème moteur diesel",
        "passage: arnaque vendeur voiture",
        "passage: documentation OpenVINO",
    ]


def test_e5_ranker_limit_keeps_best_results() -> None:
    ranker = E5LocalRanker(FakePipeline())

    result = asyncio.run(
        ranker.rank(
            E5Text.query("arnaque"),
            ["moteur", "arnaque", "autre"],
            limit=1,
        )
    )

    assert len(result.passages) == 1
    assert result.passages[0].rank == 1
    assert result.passages[0].passage.prefixed == "passage: arnaque"


def test_e5_ranker_rejects_wrong_roles() -> None:
    ranker = E5LocalRanker(FakePipeline())

    with pytest.raises(ValueError, match="query"):
        asyncio.run(ranker.rank(E5Text.passage("document"), ["passage OK"]))

    with pytest.raises(ValueError, match="passage"):
        asyncio.run(ranker.rank("question", [E5Text.query("mauvais rôle")]))


def test_e5_ranker_rejects_invalid_limit() -> None:
    ranker = E5LocalRanker(FakePipeline())

    with pytest.raises(ValueError, match="limit"):
        asyncio.run(ranker.rank("query", ["passage"], limit=0))
