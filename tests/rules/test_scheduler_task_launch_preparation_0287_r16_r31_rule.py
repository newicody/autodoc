from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_TASK_LAUNCH_PREPARATION_0287_R16_R31.md"
RULE = ROOT / "doc/code-rules/0287_r16_r31_scheduler_task_launch_preparation_rule.md"
SOURCE = ROOT / "src/kernel/scheduler_task_launch_preparation.py"
TASK_MODEL = ROOT / "src/kernel/scheduler_task_model.py"


def test_r16_r31_documents_lock_transactional_launch_boundary() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in (
        "PostgreSQL reste l’autorité durable",
        "aucune file JSON ou JSONL",
        "Aucun handler n’est instancié ni exécuté",
        "Le Dispatcher n’est pas appelé",
        "VisPy reste observation-only",
        "transaction atomique",
        "CREATED",
        "STARTED",
    ):
        assert token in architecture
    for token in (
        "ready → running",
        "command_type + capability_ref + contract_version",
        "transaction atomique",
        "Ne jamais instancier ou exécuter un handler",
        "PostgreSQL reste l’autorité durable",
        "VisPy reste observation-only",
    ):
        assert token in rule


def test_r16_r31_source_stops_before_handler_construction_and_execution() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for token in (
        "class SchedulerTaskLaunchTransaction",
        "class SchedulerHandlerLaunchTicket",
        "class SchedulerTaskLaunchPreparationService",
        "SchedulerCommandBudgetMutation",
        "catalog.resolve_for",
        "transaction.commit_launch",
        "effective_priority=decision.effective_priority",
    ):
        assert token in source
    for forbidden in (
        ".execute(",
        "Dispatcher(",
        "EventBus(",
        "json.dumps",
        "json.loads",
        "scheduler.route_requests.jsonl",
    ):
        assert forbidden not in source


def test_r16_r31_task_start_can_apply_admission_priority() -> None:
    source = TASK_MODEL.read_text(encoding="utf-8")
    assert "effective_priority: int | None = None" in source
    assert "effective_priority=next_effective_priority" in source
