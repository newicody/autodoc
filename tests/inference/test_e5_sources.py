from __future__ import annotations

import pytest

from inference.e5_corpus import E5CorpusDocument
from inference.e5_sources import (
    E5SourceDocument,
    SUPPORTED_E5_SOURCE_EXTENSIONS,
    chunk_e5_source_document,
    discover_e5_source_files,
    load_e5_corpus_documents_from_sources,
    load_e5_source_documents,
)


def test_discover_e5_source_files_filters_extensions_and_sorts(tmp_path) -> None:
    (tmp_path / "b.txt").write_text("B", encoding="utf-8")
    (tmp_path / "a.md").write_text("A", encoding="utf-8")
    (tmp_path / "ignored.py").write_text("print('no')", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "c.markdown").write_text("C", encoding="utf-8")

    files = discover_e5_source_files((tmp_path,), extensions=SUPPORTED_E5_SOURCE_EXTENSIONS)

    assert [item.name for item in files] == ["a.md", "b.txt", "c.markdown"]


def test_load_e5_source_documents_uses_relative_root_and_ignores_empty(tmp_path) -> None:
    (tmp_path / "note.md").write_text("# Titre\n\nTexte", encoding="utf-8")
    (tmp_path / "empty.txt").write_text("\n\n", encoding="utf-8")

    docs = load_e5_source_documents((tmp_path,), root=tmp_path)

    assert len(docs) == 1
    assert docs[0].path == "note.md"
    assert docs[0].metadata["source_extension"] == ".md"


def test_chunk_e5_source_document_splits_by_paragraphs() -> None:
    source = E5SourceDocument(
        path="note.md",
        text="Intro courte\n\nDeuxième paragraphe plus long\navec suite\n\nConclusion",
    )

    chunks = chunk_e5_source_document(source, max_chars=45)

    assert len(chunks) == 3
    assert chunks[0].text == "Intro courte"
    assert chunks[1].start_line == 3
    assert chunks[1].end_line == 4
    assert chunks[2].text == "Conclusion"


def test_chunk_e5_source_document_overlap_repeats_tail_paragraph() -> None:
    source = E5SourceDocument(path="note.txt", text="A\n\nB\n\nC")

    chunks = chunk_e5_source_document(source, max_chars=4, overlap_paragraphs=1)

    assert [chunk.text for chunk in chunks] == ["A\n\nB", "B\n\nC"]


def test_load_e5_corpus_documents_from_sources_produces_passages_with_metadata(tmp_path) -> None:
    (tmp_path / "note.md").write_text("Arnaque vendeur\n\nMoteur diesel", encoding="utf-8")

    docs = load_e5_corpus_documents_from_sources((tmp_path,), root=tmp_path, max_chars=20)

    assert all(isinstance(doc, E5CorpusDocument) for doc in docs)
    assert [doc.text.prefixed for doc in docs] == ["passage: Arnaque vendeur", "passage: Moteur diesel"]
    assert docs[0].metadata["source_path"] == "note.md"
    assert docs[0].metadata["chunk_index"] == 1
    assert docs[0].metadata["start_line"] == 1


def test_source_loader_rejects_invalid_options(tmp_path) -> None:
    with pytest.raises(ValueError, match="extension"):
        discover_e5_source_files((tmp_path,), extensions=())
    with pytest.raises(FileNotFoundError):
        discover_e5_source_files((tmp_path / "missing",))
    with pytest.raises(ValueError, match="max_chars"):
        chunk_e5_source_document(E5SourceDocument(path="x.md", text="x"), max_chars=0)
