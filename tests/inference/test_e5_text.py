from __future__ import annotations

import pytest

from inference.e5_text import E5Text, detect_e5_role, ensure_e5_text


def test_e5_query_adds_prefix_once() -> None:
    text = E5Text.query("comment réparer mon index vectoriel")

    assert text.role == "query"
    assert text.content == "comment réparer mon index vectoriel"
    assert text.prefixed == "query: comment réparer mon index vectoriel"
    assert text.is_query is True
    assert text.is_passage is False


def test_e5_passage_adds_prefix_once_even_if_already_prefixed() -> None:
    text = E5Text.passage("passage: document technique sur OpenVINO")

    assert text.role == "passage"
    assert text.content == "document technique sur OpenVINO"
    assert text.prefixed == "passage: document technique sur OpenVINO"


def test_e5_from_prefixed_detects_role() -> None:
    query = E5Text.from_prefixed(" query: panne zfs")
    passage = E5Text.from_prefixed("passage: notes sur zfs")

    assert query.role == "query"
    assert query.content == "panne zfs"
    assert passage.role == "passage"
    assert passage.content == "notes sur zfs"


def test_e5_from_prefixed_rejects_raw_text() -> None:
    with pytest.raises(ValueError, match="query.*passage"):
        E5Text.from_prefixed("texte brut")


def test_ensure_e5_text_respects_existing_prefix() -> None:
    text = ensure_e5_text("passage: arbre de contexte", default_role="query")

    assert text.role == "passage"
    assert text.prefixed == "passage: arbre de contexte"


def test_ensure_e5_text_uses_default_role_for_raw_text() -> None:
    text = ensure_e5_text("recherche vectorielle", default_role="query")

    assert text.role == "query"
    assert text.prefixed == "query: recherche vectorielle"


def test_detect_e5_role_is_prefix_only() -> None:
    assert detect_e5_role("query: test") == "query"
    assert detect_e5_role("passage: test") == "passage"
    assert detect_e5_role("un passage: test") is None
