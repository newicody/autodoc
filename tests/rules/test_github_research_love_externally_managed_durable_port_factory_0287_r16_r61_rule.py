from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/github_research_love_externally_managed_durable_port_factory_0287.py"
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_EXTERNALLY_MANAGED_DURABLE_PORT_FACTORY_0287_R16_R61.md"
RULE = ROOT / "doc/code-rules/0287_r16_r61_externally_managed_durable_port_factory_rule.md"


def test_r16_r61_keeps_architecture_boundaries_explicit() -> None:
    combined = ARCHITECTURE.read_text(encoding="utf-8") + "\n" + RULE.read_text(encoding="utf-8")
    assert "Scheduler canonique unique" in combined
    assert "PostgreSQL" in combined
    assert "Qdrant" in combined
    assert "384" in combined
    assert "stockage interne JSON" in combined
    assert "file JSONL" in combined
    assert "échoue" in combined


def test_r16_r61_source_does_not_open_or_construct_backends() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "open_love_postgresql_authority" not in source
    assert "build_qdrant_client_projection_executor" not in source
    assert "build_multilingual_e5_small_pipeline" not in source
    assert "Scheduler(" not in source
    assert "Dispatcher(" not in source
