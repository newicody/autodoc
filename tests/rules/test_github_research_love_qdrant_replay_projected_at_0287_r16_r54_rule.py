from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_QDRANT_REPLAY_PROJECTED_AT_0287_R16_R54.md"
RULE = ROOT / "doc/code-rules/0287_r16_r54_qdrant_replay_projected_at_rule.md"
PAIR = ROOT / "src/context/github_research_love_two_qdrant_projections_0287.py"
PROJECTOR = ROOT / "src/context/love_qdrant_live_analysis_projection_0287.py"


def test_r16_r54_documents_authority_and_json_boundaries() -> None:
    combined = ARCHITECTURE.read_text(encoding="utf-8") + RULE.read_text(encoding="utf-8")

    assert "PostgreSQL" in combined
    assert "Qdrant" in combined
    assert "384" in combined
    assert "Scheduler" in combined
    assert "file JSONL" in combined
    assert "JSON comme stockage interne" in combined


def test_r16_r54_reuses_one_projection_identity_builder() -> None:
    pair = PAIR.read_text(encoding="utf-8")
    projector = PROJECTOR.read_text(encoding="utf-8")

    assert "build_love_qdrant_live_projection_identity_from_refs" in pair
    assert "build_love_qdrant_live_projection_identity_from_refs" in projector
    assert "isinstance(first_object, ContextAuthorityObject)" not in pair
    assert "existing immutable projections disagree on projected_at" in pair
    assert "projected_at=projected_at" in pair
