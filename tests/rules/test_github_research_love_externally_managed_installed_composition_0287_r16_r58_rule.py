from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_research_love_externally_managed_installed_composition_0287.py"
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_EXTERNALLY_MANAGED_INSTALLED_COMPOSITION_0287_R16_R58.md"
RULE = ROOT / "doc/code-rules/0287_r16_r58_externally_managed_installed_composition_rule.md"


def test_r16_r58_keeps_architecture_boundaries_explicit() -> None:
    combined = ARCHITECTURE.read_text(encoding="utf-8") + "\n" + RULE.read_text(
        encoding="utf-8"
    )
    for value in (
        "Scheduler canonique unique",
        "PostgreSQL",
        "Qdrant",
        "OpenVINO",
        "OpenRC",
        "externally-managed",
        "dix handlers",
        "file JSONL",
        "stockage interne JSON",
    ):
        assert value in combined


def test_r16_r58_does_not_create_parallel_runtime_authorities() -> None:
    source = MODULE.read_text(encoding="utf-8")
    assert "build_github_research_love_full_grouped_scheduler_bootstrap" in source
    assert "SchedulerCanonicalBoundedCycle" in source
    assert "PriorityQueue(" not in source
    assert "Dispatcher(" not in source
    assert "EventBus(" not in source
    assert "json.dumps" not in source
    assert ".jsonl" not in source
    assert "LaboratoryManager" not in source
