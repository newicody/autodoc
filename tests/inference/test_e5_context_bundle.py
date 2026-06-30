from __future__ import annotations

from inference.e5_context_bundle import E5ContextBundle
from inference.e5_search_report import (
    E5SearchReport,
    E5SearchReportConfig,
    E5SearchReportHit,
    E5SearchSourceContext,
)


def _report() -> E5SearchReport:
    return E5SearchReport(
        query="OpenVINO local",
        prefixed_query="query: OpenVINO local",
        index="/tmp/corpus.json",
        model="openvino.embedding.e5-small",
        backend="openvino.embedding.e5-small",
        tokenizer="transformers.multilingual-e5-small",
        dimension=384,
        hits=(
            E5SearchReportHit(
                rank=1,
                id="chunk-1",
                score=0.91,
                source=E5SearchSourceContext(
                    source_path="README.md",
                    start_line=10,
                    end_line=12,
                    chunk_index=0,
                ),
                excerpt="OpenVINO E5 local search",
                text="OpenVINO E5 local search full text",
            ),
        ),
        config=E5SearchReportConfig(),
    )


def test_context_bundle_from_search_report_is_stable() -> None:
    bundle = E5ContextBundle.from_search_report(_report())

    assert bundle.item_count == 1
    assert bundle.items[0].source_path == "README.md"
    assert bundle.items[0].line_range == "10-12"
    assert bundle.to_json_dict() == {
        "query": "OpenVINO local",
        "prefixed_query": "query: OpenVINO local",
        "index": "/tmp/corpus.json",
        "model": "openvino.embedding.e5-small",
        "backend": "openvino.embedding.e5-small",
        "tokenizer": "transformers.multilingual-e5-small",
        "dimension": 384,
        "item_count": 1,
        "items": [
            {
                "rank": 1,
                "id": "chunk-1",
                "score": 0.91,
                "source_path": "README.md",
                "line_range": "10-12",
                "chunk_index": 0,
                "excerpt": "OpenVINO E5 local search",
            }
        ],
    }


def test_context_bundle_text_output_is_compact() -> None:
    text = E5ContextBundle.from_search_report(_report()).to_text()

    assert "query: OpenVINO local" in text
    assert "context_item_count: 1" in text
    assert "[1] README.md:10-12" in text
    assert "OpenVINO E5 local search" in text
