from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/context_revision_task_impact_0287.py"
CURRENT = ROOT / "doc/README_CURRENT.md"
ARCHITECTURE = (
    ROOT
    / "doc/architecture/CONTEXT_REVISION_TASK_IMPACT_0287_R7_R8_R5.md"
)
REPORT = ROOT / "PHASE0287_R7_R8_R5_CONTEXT_REVISION_TASK_IMPACT_REPORT.md"


def test_context_revision_task_impact_contract_is_versioned_and_scheduler_owned() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    for token in (
        "missipy.context.revision_change_set.v1",
        "missipy.context.task_binding.v1",
        "missipy.context.task_impact_assessment.v1",
        "missipy.scheduler.context_impact_decision.v1",
        "snapshot",
        "checkpoint_rebase",
        "restart_on_material_change",
        "fork_on_material_change",
        "notify_only",
        "ignore_noncritical",
        "scheduler_authority_required",
        '"action_executed": False',
        '"route_changed": False',
    ):
        assert token in text


def test_controlproxy_is_not_promoted_to_context_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "ControlProxy route" in text
    assert '"controlproxy_is_transport_only": True' in text
    assert "from context.route_generation" not in text
    assert "from runtime" not in text


def test_roadmap_and_architecture_lock_the_next_transport_boundary() -> None:
    current = CURRENT.read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")

    for token in (
        "0287-r7-r8-r5",
        "SQL semantic revision",
        "Scheduler decision",
        "ControlProxy remains transport-only",
        "0287-r7-r8-r6",
    ):
        assert token in current or token in architecture or token in report
