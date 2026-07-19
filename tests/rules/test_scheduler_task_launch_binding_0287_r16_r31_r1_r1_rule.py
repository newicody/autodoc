from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_TASK_LAUNCH_BINDING_0287_R16_R31_R1_R1.md"
RULE = ROOT / "doc/code-rules/0287_r16_r31_r1_r1_scheduler_task_launch_binding_rule.md"
SOURCE = ROOT / "src/context/love_postgresql_authority_binding_0287.py"


def test_r16_r31_r1_r1_locks_shared_postgresql_connection_boundary() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")

    for token in (
        "La même connexion DB-API",
        "Aucune connexion supplémentaire",
        "aucune file JSONL",
        "VisPy restent observation-only",
        "runtime `tool-bounded` historique n’est pas étendu",
    ):
        assert token in architecture

    for token in (
        "Réutiliser exactement la connexion",
        "Initialiser le schéma de lancement",
        "Ne pas démarrer le Scheduler",
        "Ne stocker aucune autorité en JSON ou JSONL",
    ):
        assert token in rule

    assert "DbApiSchedulerTaskLaunchTransaction" in source
    assert "scheduler_task_launch_transaction" in source
    assert "scheduler_task_launch_transaction.initialize_schema()" in source
    assert "scheduler_task_launch_uses_owned_connection" in source
    assert "Scheduler(" not in source
    assert "Dispatcher(" not in source
