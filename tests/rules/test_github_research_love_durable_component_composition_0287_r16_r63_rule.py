from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/github_research_love_externally_managed_durable_component_composition_0287.py"
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_DURABLE_COMPONENT_COMPOSITION_0287_R16_R63.md"
RULE = ROOT / "doc/code-rules/0287_r16_r63_durable_component_composition_rule.md"


def test_r16_r63_documents_the_architecture_boundaries() -> None:
    combined = (
        ARCHITECTURE.read_text(encoding="utf-8")
        + "\n"
        + RULE.read_text(encoding="utf-8")
    )
    assert "Scheduler canonique unique" in combined
    assert "PostgreSQL" in combined
    assert "Qdrant" in combined
    assert "OpenRC" in combined
    assert "384" in combined
    assert "stockage interne JSON" in combined
    assert "file JSONL" in combined
    assert "échoue fermé" in combined


def test_r16_r63_source_reuses_boundaries_without_opening_backends() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "build_github_research_love_externally_managed_postgresql_adapter_boundary" in source
    assert "boundary.adapter_port is not foundation.postgresql_adapter_port" in source
    assert "open_love_postgresql_authority" not in source
    assert "build_qdrant_client_projection_executor" not in source
    assert "build_multilingual_e5_small_pipeline" not in source
    assert "Scheduler(" not in source
    assert "Dispatcher(" not in source
