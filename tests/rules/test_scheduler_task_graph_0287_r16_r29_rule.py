from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_TASK_GRAPH_0287_R16_R29.md"
RULE = ROOT / "doc/code-rules/0287_r16_r29_scheduler_task_graph_rule.md"
SOURCE = ROOT / "src/kernel/scheduler_task_graph.py"


def test_r16_r29_docs_lock_graph_boundary() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "graphe immuable",
        "ordre stable",
        "portes de branche `ANY` et `ALL`",
        "aucun handler",
        "PostgreSQL",
    ]:
        assert token in architecture
    for token in [
        "Détecter les cycles",
        "Ne jamais promouvoir une tâche",
        "Le plan de readiness reste pur",
        "Ne pas appeler le Dispatcher",
    ]:
        assert token in rule


def test_r16_r29_source_has_no_side_effect_boundary() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for forbidden in [
        "json.dumps",
        "json.loads",
        "open(",
        "subprocess",
        "EventBus",
        "Dispatcher(",
        "asyncio.run",
        "print(",
    ]:
        assert forbidden not in source
    assert "class SchedulerTaskGraph" in source
    assert "class SchedulerTaskBranchGate" in source
    assert "class SchedulerTaskBarrier" in source
