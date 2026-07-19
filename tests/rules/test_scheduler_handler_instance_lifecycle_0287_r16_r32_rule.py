from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_HANDLER_INSTANCE_LIFECYCLE_0287_R16_R32.md"
RULE = ROOT / "doc/code-rules/0287_r16_r32_scheduler_handler_instance_lifecycle_rule.md"
SOURCE = ROOT / "src/kernel/scheduler_handler_instance_lifecycle.py"


def test_r16_r32_locks_real_instance_and_information_boundary() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")

    for token in (
        "instance réelle",
        "notice CREATED",
        "notice STARTED",
        "arrêt avant handler.execute()",
        "VisPy reste observation-only",
        "Aucune file JSON ou JSONL",
    ):
        assert token in architecture

    for token in (
        "ticket de lancement déjà commité",
        "fabrique explicitement injectée",
        "Ne jamais appeler `handler.execute()`",
        "panne du sink informatif",
        "notices de fin",
    ):
        assert token in rule

    for forbidden in (
        "import json",
        "Dispatcher(",
        "EventBus(",
        ".execute(ticket.command",
        "asyncio.create_task",
    ):
        assert forbidden not in source
