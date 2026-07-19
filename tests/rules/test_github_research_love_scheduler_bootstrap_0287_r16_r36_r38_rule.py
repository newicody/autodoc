from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_research_love_scheduler_bootstrap_0287.py"
DOC = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_SCHEDULER_BOOTSTRAP_0287_R16_R36_R38.md"
RULE = ROOT / "doc/code-rules/0287_r16_r36_r38_github_research_love_scheduler_bootstrap_rule.md"


def test_r16_r36_r38_locks_reuse_and_scheduler_authority() -> None:
    source = MODULE.read_text(encoding="utf-8")
    architecture = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")

    assert "build_first_love_visit_surface_from_github_research" in source
    assert "dispatch_first_love_visit_from_github_research" not in source
    assert "submit_native_love_collaboration_visit" not in source
    assert "SchedulerHandlerCatalog" in source
    assert "ExplicitSchedulerHandlerFactory" in source
    assert "SchedulerTaskGraph.create" in source
    assert "quatorze" in architecture
    assert "Scheduler reste l’unique autorité" in architecture
    assert "VisPy reste observation-only" in architecture
    assert "Ne cataloguer que les capacités réellement exécutables" in rule
    assert "aucun Scheduler parallèle" in rule
