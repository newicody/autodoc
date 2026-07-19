from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_HANDLER_EXECUTION_BINDING_0287_R16_R33_R1_R1.md"
RULE = ROOT / "doc/code-rules/0287_r16_r33_r1_r1_scheduler_handler_execution_binding_rule.md"
SOURCE = ROOT / "src/context/love_postgresql_authority_binding_0287.py"


def test_r16_r33_r1_r1_locks_shared_completion_transaction_boundary() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")

    for token in (
        "La même connexion DB-API",
        "Aucune autorité n’est stockée en JSON ou JSONL",
        "ne recalcule pas le graphe",
        "VisPy restent observation-only",
        "unité r16-r34",
    ):
        assert token in architecture

    for token in (
        "Réutiliser exactement la connexion",
        "Initialiser le schéma de fin d’exécution",
        "Ne pas rejouer le handler",
        "Ne stocker aucune autorité en JSON ou JSONL",
    ):
        assert token in rule

    for token in (
        "DbApiSchedulerHandlerExecutionTransaction",
        "scheduler_handler_execution_transaction",
        "scheduler_handler_execution_schema_initialized",
        '"scheduler_handler_execution_replayed": False',
    ):
        assert token in source
