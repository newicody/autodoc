from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_HANDLER_CONTROLLED_EXECUTION_0287_R16_R33.md"
RULE = ROOT / "doc/code-rules/0287_r16_r33_scheduler_handler_controlled_execution_rule.md"
SOURCE = ROOT / "src/kernel/scheduler_handler_execution.py"
MODEL = ROOT / "src/kernel/scheduler_task_model.py"


def test_r16_r33_documents_lock_controlled_execution_boundary() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in (
        "exactement une fois `handler.execute()`",
        "PostgreSQL reste l'autorité durable",
        "aucune file JSON ou JSONL",
        "fermeture est explicitement injectée et toujours tentée",
        "VisPy reste",
        "observation-only",
        "transaction de fin appartient à r16-r33-r1",
    ):
        assert token in architecture
    for token in (
        "Ne jamais laisser le handler décider du retry",
        "Toujours tenter la fermeture",
        "ne réécrit pas le résultat métier",
        "Ne créer aucun Scheduler, Dispatcher, EventBus",
        "traces d'objets temporaires",
    ):
        assert token in rule


def test_r16_r33_source_uses_typed_outcomes_without_internal_json_storage() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    model = MODEL.read_text(encoding="utf-8")
    for token in (
        "class SchedulerHandlerExecutionOutcome",
        "class SchedulerHandlerExecutionService",
        "class SchedulerHandlerFailureClassifier",
        "class SchedulerHandlerResultProjector",
        "class SchedulerHandlerCloser",
        "SchedulerTaskAttemptCompletion",
        "SchedulerTaskAttemptFailureOutcome",
        "SchedulerTaskAttemptInterruption",
        "await closer.close",
    ):
        assert token in source
    for forbidden in (
        "json.dumps",
        "json.loads",
        "Dispatcher(",
        "EventBus(",
        "Scheduler(",
    ):
        assert forbidden not in source
    assert "def cancel_attempt(" in model
    assert "def timeout_attempt(" in model
    assert "class SchedulerTaskAttemptInterruption" in model
