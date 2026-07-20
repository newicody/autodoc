from __future__ import annotations

from pathlib import Path

import context.github_research_love_final_deliverable_sql_0287 as module


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = ROOT / (
    "doc/architecture/"
    "GITHUB_RESEARCH_LOVE_FINAL_DELIVERABLE_SQL_REPLAY_CREATED_AT_0287_R16_R55.md"
)
RULE = ROOT / (
    "doc/code-rules/"
    "0287_r16_r55_final_deliverable_sql_replay_created_at_rule.md"
)


def test_r16_r55_keeps_architecture_boundaries_explicit() -> None:
    combined = (
        ARCHITECTURE.read_text(encoding="utf-8")
        + "\n"
        + RULE.read_text(encoding="utf-8")
    )
    assert "Scheduler canonique unique" in combined
    assert "PostgreSQL" in combined
    assert "Qdrant" in combined
    assert "file JSONL" in combined
    assert "mapping complet" in combined
    assert "échec fermé" in combined


def test_r16_r55_reuses_first_timestamp_without_weakening_comparison() -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "_resolve_final_deliverable_created_at(" in source
    assert source.count("created_at=persistence_created_at") == 2
    assert "existing_mapping() == expected_mapping()" in source
    assert "store.get_artifact(artifact_ref)" in source
    assert "store.get_revision(revision_ref)" in source
    assert "delete" not in source.lower()
