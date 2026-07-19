from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_TASK_LAUNCH_SQL_AUTHORITY_0287_R16_R31_R1.md"
RULE = ROOT / "doc/code-rules/0287_r16_r31_r1_scheduler_task_launch_sql_authority_rule.md"
SOURCE = ROOT / "src/context/scheduler_task_launch_sql_authority_0287.py"


def test_r16_r31_r1_documents_lock_atomic_relational_boundary() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    for token in (
        "connexion DB-API déjà possédée",
        "rollback complet",
        "PostgreSQL reste l’autorité durable",
        "aucune colonne JSON",
        "VisPy restent observation-only",
    ):
        assert token in architecture
    for token in (
        "Refuser l’autocommit",
        "transaction atomique",
        "rejeu exact idempotent",
        "sans JSON ni JSONL",
        "Ne pas instancier ou exécuter de handler",
    ):
        assert token in rule
    for token in (
        "class DbApiSchedulerTaskLaunchTransaction",
        "def commit_launch(",
        "self._connection.commit()",
        "self._rollback_quietly()",
        "scheduler_task_launch_transactions",
    ):
        assert token in source
