from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_EXTERNALLY_MANAGED_COMPONENT_BINDING_0287_R16_R60.md"
RULE = ROOT / "doc/code-rules/0287_r16_r60_externally_managed_component_binding_rule.md"
SOURCE = ROOT / "src/context/github_research_love_externally_managed_component_binding_0287.py"
CONFIG = ROOT / "config/github_research_love_externally_managed_components.example.env"


def test_r16_r60_documents_architecture_boundaries() -> None:
    combined = ARCHITECTURE.read_text(encoding="utf-8") + "\n" + RULE.read_text(
        encoding="utf-8"
    )
    for token in (
        "Scheduler canonique unique",
        "PostgreSQL",
        "Qdrant",
        "OpenVINO",
        "OpenRC",
        "file JSONL",
        "stockage interne JSON",
        "observation-only",
    ):
        assert token in combined


def test_r16_r60_keeps_factories_explicit_and_source_without_parallel_backend() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    assert "AUTODOC_GITHUB_RESEARCH_EXTERNALLY_MANAGED_DURABLE_PORT_FACTORY" in source
    assert "AUTODOC_GITHUB_RESEARCH_EXTERNALLY_MANAGED_COMPONENT_FACTORY" in config
    assert "AUTODOC_GITHUB_RESEARCH_OPENRC_SERVICE_FACTORY" in config
    assert 'AUTODOC_GITHUB_RESEARCH_EXTERNALLY_MANAGED_DURABLE_PORT_FACTORY=""' in config
    for forbidden in (
        "Scheduler(",
        "Dispatcher(",
        "EventBus(",
        "import json",
        "jsonlines",
        "JSONLWriter",
    ):
        assert forbidden not in source
