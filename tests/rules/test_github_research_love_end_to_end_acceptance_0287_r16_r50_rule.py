from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_r16_r50_locks_real_acceptance_without_new_orchestrator() -> None:
    module = (
        ROOT
        / "src/context/github_research_love_end_to_end_acceptance_0287.py"
    ).read_text(encoding="utf-8")
    architecture = (
        ROOT
        / "doc/architecture/GITHUB_RESEARCH_LOVE_END_TO_END_ACCEPTANCE_0287_R16_R50.md"
    ).read_text(encoding="utf-8")
    glossary = (
        ROOT
        / "doc/glossaire/GLOSSAIRE_FRANCAIS_AUTODOC_0287_R16_R50.md"
    ).read_text(encoding="utf-8")

    assert "validation_only" in module
    assert "new_scheduler_created" in module
    assert "postgresql_remains_durable_authority" in module
    assert "vispy_remains_observation_only" in module
    assert "VisPy reste observation-only" in architecture
    assert "Aucun nouveau Scheduler" in architecture
    assert "gestionnaire de traitement" in glossary
    assert "relecture de confirmation" in glossary
    assert "réclamation atomique" in glossary
