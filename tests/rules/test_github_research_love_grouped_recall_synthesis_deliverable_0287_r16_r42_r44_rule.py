from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/github_research_love_grouped_recall_synthesis_deliverable_0287.py"
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_RECALL_SYNTHESIS_DELIVERABLE_0287_R16_R42_R44.md"
RULE = ROOT / "doc/code-rules/0287_r16_r42_r44_grouped_recall_synthesis_deliverable_rule.md"


def test_r16_r42_r44_reuses_existing_compositions_and_stops_before_publication() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "recall_github_research_love_analyses" in source
    assert "build_github_research_love_liaison_synthesis" in source
    assert "persist_github_research_love_final_deliverable" in source
    assert "SchedulerHandlerCatalog(handler_types)" in source
    assert "publish_github" not in source
    assert "subprocess" not in source
    assert "jsonl" not in source.lower()


def test_r16_r42_r44_documents_authorities_and_observation_boundary() -> None:
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    assert "PostgreSQL demeure l'autorité durable" in architecture
    assert "Qdrant reste un index" in architecture
    assert "VisPy reste\nobservation-only" in architecture
    assert "Persister le livrable local avant toute mutation GitHub" in rule
    assert "Ne pas cataloguer encore les capacités de publication" in rule
