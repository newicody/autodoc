from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/kernel/scheduler_task_model.py"
ARCH = ROOT / "doc/architecture/SCHEDULER_TASK_MODEL_0287_R16_R28.md"
RULE = ROOT / "doc/code-rules/0287_r16_r28_scheduler_task_model_rule.md"


def test_r16_r28_files_exist_and_lock_typed_task_structure() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")

    for token in (
        "class SchedulerTaskState",
        "class SchedulerTaskDependency",
        "class SchedulerTaskTransition",
        "class SchedulerTaskAttempt",
        "class SchedulerTaskResult",
        "class SchedulerTaskFailure",
        "class SchedulerTask:",
    ):
        assert token in source

    for token in (
        "Une commande représente une mission durable",
        "aucun dictionnaire ou JSON comme autorité interne",
        "ready → running",
        "running → completed",
        "running → failed/retry-wait",
    ):
        assert token in architecture

    for token in (
        "Une commande est la mission durable",
        "Une tâche est une unité exécutable créée par le Scheduler",
        "Une tentative est l'exécution concrète d'un handler",
        "Ne pas utiliser JSON, JSONL ou des dictionnaires comme autorité interne",
        "Un handler ne crée pas directement la tâche suivante",
    ):
        assert token in rule


def test_r16_r28_model_has_no_external_effect_boundary() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "import json",
        "from json",
        "psycopg",
        "qdrant",
        "EventBus",
        "Dispatcher",
        "ControlProxy",
        "subprocess",
        "print(",
        "open(",
    )
    for token in forbidden:
        assert token not in source


def test_r16_r28_rule_keeps_scheduler_as_transition_authority() -> None:
    rule = RULE.read_text(encoding="utf-8")
    assert "créée par le Scheduler" in rule
    assert "Produire une `SchedulerTaskTransition` digestée" in rule
    assert "Ne planifier un retry" in rule
    assert "afficher aucun texte automatiquement" in rule
