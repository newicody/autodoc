from __future__ import annotations

from inference.e5_corpus import E5CorpusDocument
from inference.e5_sources import (
    DEFAULT_E5_EXCLUDED_DIR_NAMES,
    DEFAULT_E5_EXCLUDED_FILE_SUFFIXES,
    E5SourceDiscoveryConfig,
    discover_e5_source_files,
    load_e5_corpus_documents_from_sources,
)


def test_default_source_hygiene_skips_cache_and_git_directories(tmp_path) -> None:
    (tmp_path / "visible.md").write_text("Visible", encoding="utf-8")

    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "ignored.md").write_text("Git internals", encoding="utf-8")

    cache_dir = tmp_path / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "ignored.txt").write_text("Cache", encoding="utf-8")

    files = discover_e5_source_files((tmp_path,))

    assert [item.name for item in files] == ["visible.md"]


def test_source_hygiene_skips_excluded_file_suffix_even_when_extension_matches(tmp_path) -> None:
    (tmp_path / "diagram.svg").write_text("<svg />", encoding="utf-8")
    (tmp_path / "note.md").write_text("Note", encoding="utf-8")

    files = discover_e5_source_files((tmp_path,), extensions=(".md", ".svg"))

    assert [item.name for item in files] == ["note.md"]


def test_source_hygiene_accepts_custom_excluded_directory(tmp_path) -> None:
    (tmp_path / "visible.md").write_text("Visible", encoding="utf-8")

    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    (generated_dir / "ignored.md").write_text("Generated", encoding="utf-8")

    files = discover_e5_source_files(
        (tmp_path,),
        excluded_dir_names=(*DEFAULT_E5_EXCLUDED_DIR_NAMES, "generated"),
    )

    assert [item.name for item in files] == ["visible.md"]


def test_source_hygiene_accepts_custom_excluded_suffix(tmp_path) -> None:
    (tmp_path / "draft.md").write_text("Draft", encoding="utf-8")
    (tmp_path / "published.md").write_text("Published", encoding="utf-8")

    files = discover_e5_source_files(
        (tmp_path,),
        excluded_file_suffixes=(*DEFAULT_E5_EXCLUDED_FILE_SUFFIXES, "draft.md"),
    )

    assert [item.name for item in files] == ["published.md"]


def test_load_e5_corpus_documents_from_sources_uses_default_hygiene(tmp_path) -> None:
    (tmp_path / "note.md").write_text("Visible passage", encoding="utf-8")

    cache_dir = tmp_path / ".pytest_cache"
    cache_dir.mkdir()
    (cache_dir / "ignored.md").write_text("Cache passage", encoding="utf-8")

    docs = load_e5_corpus_documents_from_sources((tmp_path,), root=tmp_path)

    assert all(isinstance(doc, E5CorpusDocument) for doc in docs)
    assert [doc.text.prefixed for doc in docs] == ["passage: Visible passage"]
    assert docs[0].metadata["source_path"] == "note.md"


def test_source_discovery_config_normalizes_values() -> None:
    config = E5SourceDiscoveryConfig(
        extensions=("md", " .TXT "),
        excluded_dir_names=("", "build", " dist "),
        excluded_file_suffixes=("pyc", " .SVG "),
    )

    assert config.normalized_extensions == frozenset((".md", ".txt"))
    assert config.normalized_excluded_dir_names == frozenset(("build", "dist"))
    assert config.normalized_excluded_file_suffixes == frozenset((".pyc", ".svg"))
