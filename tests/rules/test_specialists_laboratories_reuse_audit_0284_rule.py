from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/specialists_laboratories_reuse_audit_0284.py"
DOC = ROOT / "doc/architecture/SPECIALISTS_LABORATORIES_REUSE_AUDIT_0284.md"
REPORT = ROOT / "PHASE0284_R1_SPECIALISTS_LABORATORIES_REUSE_AUDIT_REPORT.md"

def test_no_parallel_orchestrator_is_introduced():
    source = MODULE.read_text(encoding="utf-8")
    assert "class LaboratoryManager" not in source
    assert "class Scheduler" not in source
    for token in (
        '("new_laboratory_manager_allowed", False)',
        '("new_scheduler_allowed", False)',
        '("new_parallel_queue_allowed", False)',
        '("new_parallel_bus_allowed", False)',
    ):
        assert token in source

def test_audit_documents_locked_boundaries():
    combined = DOC.read_text(encoding="utf-8") + REPORT.read_text(encoding="utf-8")
    for token in (
        "scheduler_remains_only_orchestrator: true",
        "new_laboratory_manager_allowed: false",
        "event_bus_remains_observation_only: true",
        "sql_remains_durable_authority: true",
        "qdrant_remains_projection_and_recall: true",
        "control_proxy_is_lateral_only: true",
        "projects_repository_change_required: false",
        "0284-r2-specialist-portable-execution-envelope",
    ):
        assert token in combined
