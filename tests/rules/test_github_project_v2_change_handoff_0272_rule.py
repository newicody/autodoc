from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src/context/github_project_v2_change_handoff_0272.py"
CLI = ROOT / "tools/build_github_project_v2_change_handoffs_0272.py"
SCHEDULER = ROOT / "src/kernel/scheduler.py"


def test_0272_r6_reuses_source_candidate_and_keeps_boundaries_closed() -> None:
    core = CORE.read_text(encoding="utf-8")
    cli = CLI.read_text(encoding="utf-8")
    assert "from context.source_candidate import" in core
    assert "build_source_candidate" in core
    assert "urllib" not in core
    assert "requests" not in core
    assert "qdrant" not in core.lower() or '"qdrant_write_allowed": False' in core
    assert "sql_write_allowed" in core
    assert "remote_mutation_allowed" in core
    assert "max_handoffs" in core
    assert "configparser" in cli
    assert "urlopen" not in cli


def test_0272_r6_does_not_modify_scheduler_run() -> None:
    if SCHEDULER.exists():
        scheduler = SCHEDULER.read_text(encoding="utf-8")
        assert "def run" in scheduler
    assert "scheduler_modified\": False" in CORE.read_text(encoding="utf-8")
