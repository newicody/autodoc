from __future__ import annotations

import pytest

from inference.e5_context_bundle import E5ContextBundle, E5ContextBundleItem
from inference.e5_context_consumer import (
    E5ContextConsumptionPolicy,
    consume_e5_context_bundle,
)


def _bundle() -> E5ContextBundle:
    return E5ContextBundle(
        query="OpenVINO local",
        prefixed_query="query: OpenVINO local",
        index="/tmp/corpus.json",
        model="openvino.embedding.e5-small",
        backend="openvino.embedding.e5-small",
        tokenizer="transformers.multilingual-e5-small",
        dimension=384,
        items=(
            E5ContextBundleItem(
                rank=1,
                id="a",
                score=0.91,
                source_path="doc/a.md",
                line_range="10-12",
                chunk_index=0,
                excerpt="OpenVINO E5 local search",
            ),
            E5ContextBundleItem(
                rank=2,
                id="b",
                score=0.82,
                source_path="doc/b.md",
                line_range="20-22",
                chunk_index=1,
                excerpt="Scheduler compatible context bundle",
            ),
        ),
    )


def test_consume_e5_context_bundle_selects_ranked_items_within_budget() -> None:
    result = consume_e5_context_bundle(_bundle(), E5ContextConsumptionPolicy(max_chars=200, max_items=1))

    assert result.available_item_count == 2
    assert result.selected_item_count == 1
    assert result.skipped_item_count == 1
    assert result.used_chars <= 200
    assert result.context_text == "[1] doc/a.md:10-12\nOpenVINO E5 local search"


def test_consume_e5_context_bundle_json_is_stable() -> None:
    result = consume_e5_context_bundle(
        _bundle(),
        E5ContextConsumptionPolicy(max_chars=200, max_items=1, include_scores=True),
    )

    assert result.to_json_dict() == {
        "query": "OpenVINO local",
        "prefixed_query": "query: OpenVINO local",
        "max_chars": 200,
        "used_chars": len("[1] doc/a.md:10-12\nscore: 0.91000000\nOpenVINO E5 local search"),
        "available_item_count": 2,
        "selected_item_count": 1,
        "skipped_item_count": 1,
        "context_text": "[1] doc/a.md:10-12\nscore: 0.91000000\nOpenVINO E5 local search",
        "items": [
            {
                "rank": 1,
                "id": "a",
                "score": 0.91,
                "source_path": "doc/a.md",
                "line_range": "10-12",
                "chunk_index": 0,
                "text": "[1] doc/a.md:10-12\nscore: 0.91000000\nOpenVINO E5 local search",
            }
        ],
    }


def test_consume_e5_context_bundle_respects_character_budget() -> None:
    result = consume_e5_context_bundle(_bundle(), E5ContextConsumptionPolicy(max_chars=20))

    assert result.selected_item_count == 0
    assert result.skipped_item_count == 2
    assert result.used_chars == 0
    assert result.context_text == ""


def test_context_consumption_policy_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="max_chars"):
        E5ContextConsumptionPolicy(max_chars=0)
    with pytest.raises(ValueError, match="max_items"):
        E5ContextConsumptionPolicy(max_items=0)
