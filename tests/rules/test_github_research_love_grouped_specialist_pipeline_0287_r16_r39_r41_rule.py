from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_research_love_grouped_specialist_pipeline_0287.py"
DOC = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_GROUPED_SPECIALIST_PIPELINE_0287_R16_R39_R41.md"
RULE = ROOT / "doc/code-rules/0287_r16_r39_r41_grouped_specialist_pipeline_rule.md"


def test_r16_r39_r41_locks_grouped_but_distinct_pipeline() -> None:
    source = MODULE.read_text(encoding="utf-8")
    architecture = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in (
        "dispatch_first_love_visit_from_github_research",
        "dispatch_second_love_visit_from_first_analysis",
        "persist_github_research_love_analyses",
        "project_github_research_love_analyses",
        "SchedulerHandlerCatalog",
        "ExplicitSchedulerHandlerFactory",
    ):
        assert token in source
    assert "Scheduler(" not in source
    assert "Dispatcher(" not in source
    assert "EventBus(" not in source
    assert "384" in architecture
    assert "deux analyses" in architecture
    assert "VisPy reste observation-only" in architecture
    assert "PostgreSQL avant toute projection" in rule
    assert "deux projections Qdrant distincts" in rule
