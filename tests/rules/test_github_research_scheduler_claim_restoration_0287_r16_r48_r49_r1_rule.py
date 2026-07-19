from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLAIM = ROOT / "src/context/github_research_scheduler_command_claim_0287.py"
SQL = ROOT / "src/context/github_research_scheduler_command_sql_authority_0287.py"
RUNTIME = ROOT / "src/context/github_research_love_externally_managed_runtime_0287.py"


def test_claim_boundary_required_by_external_runtime_is_present() -> None:
    claim = CLAIM.read_text(encoding="utf-8")
    sql = SQL.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    assert "claim_next_for_running_canonical_scheduler" in claim
    assert "scheduler.running is not True" in claim
    assert "def claim_next_pending(" in sql
    assert "FOR UPDATE OF s SKIP LOCKED" in sql
    assert "from context.github_research_scheduler_command_claim_0287" in runtime
    for forbidden in ("Scheduler(", "while True", "jsonl", "LaboratoryManager"):
        assert forbidden not in claim
