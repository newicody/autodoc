from __future__ import annotations

import pytest

from inference.e5_corpus import E5CorpusSearchHit, E5CorpusSearchResults
from inference.e5_search_report import (
    E5SearchReport,
    E5SearchReportConfig,
    E5SearchSourceContext,
    make_excerpt,
)
from inference.e5_text import E5Text


def test_make_excerpt_collapses_whitespace_and_truncates() -> None:
    text = "Ligne une\n\nligne deux avec beaucoup de texte"

    assert make_excerpt(text, max_chars=18) == "Ligne une ligne d…"
    assert make_excerpt(" texte  court ", max_chars=30) == "texte court"
    with pytest.raises(ValueError, match="positive"):
        make_excerpt("x", max_chars=0)


def test_source_context_extracts_line_range_from_metadata() -> None:
    context = E5SearchSourceContext.from_metadata(
        {
            "source_path": "notes/garage.md",
            "start_line": "12",
            "end_line": 18,
            "chunk_index": 3,
            "source_id": "source-abc",
            "source_extension": ".md",
        }
    )

    assert context.has_source is True
    assert context.line_range == "12-18"
    assert context.to_json_dict()["source_path"] == "notes/garage.md"
    assert context.to_text() == ("source: notes/garage.md", "lines: 12-18", "chunk: 3")


def test_search_report_adds_source_context_and_excerpt() -> None:
    hit = E5CorpusSearchHit(
        rank=1,
        id="doc-1",
        score=0.75,
        text="Un vendeur a arnaqué le client pendant une transaction.",
        prefixed_text="passage: Un vendeur a arnaqué le client pendant une transaction.",
        metadata={"source_path": "notes/litige.md", "start_line": 4, "end_line": 6, "chunk_index": 1},
    )
    results = E5CorpusSearchResults(
        query=E5Text.query("je me suis fait baiser"),
        model="m",
        backend="b",
        tokenizer="t",
        dimension=384,
        hits=(hit,),
    )

    report = E5SearchReport.from_results(
        query=results.query.content,
        prefixed_query=results.query.prefixed,
        index="/tmp/corpus.json",
        results=results,
        config=E5SearchReportConfig(excerpt_chars=32),
    )

    assert report.to_json_dict()["hits"][0]["source"]["line_range"] == "4-6"
    text = report.to_text()
    assert "source: notes/litige.md" in text
    assert "lines: 4-6" in text
    assert "excerpt: Un vendeur a arnaqué le client…" in text
    assert "text:" not in text


def test_search_report_can_include_full_text() -> None:
    hit = E5CorpusSearchHit(
        rank=1,
        id="doc-1",
        score=1.0,
        text="Texte complet",
        prefixed_text="passage: Texte complet",
    )
    results = E5CorpusSearchResults(
        query=E5Text.query("q"),
        model="m",
        backend="b",
        tokenizer="t",
        dimension=2,
        hits=(hit,),
    )

    report = E5SearchReport.from_results(
        query="q",
        prefixed_query="query: q",
        index="corpus.json",
        results=results,
        config=E5SearchReportConfig(include_full_text=True),
    )

    assert report.to_json_dict()["hits"][0]["text"] == "Texte complet"
    assert "text: Texte complet" in report.to_text()
