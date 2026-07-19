from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_TASK_ADMISSION_0287_R16_R30.md"
RULE = ROOT / "doc/code-rules/0287_r16_r30_scheduler_task_admission_rule.md"
SOURCE = ROOT / "src/kernel/scheduler_task_admission.py"


def test_r16_r30_documents_lock_pure_scheduler_admission_boundary() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    for token in (
        "PostgreSQL reste l’autorité durable",
        "aucune file JSON ou JSONL",
        "prévention de famine",
        "aucun handler n’est exécuté",
        "VisPy reste observation-only",
    ):
        assert token in architecture
    for token in (
        "Le planificateur ne modifie jamais SchedulerTask",
        "Le budget global de commande",
        "Le profil de ressources",
        "Le backoff est entier, déterministe et borné",
        "Le Scheduler vivant applique seul le plan",
    ):
        assert token in rule
    assert "class SchedulerTaskAdmissionPlanner" in source
    assert "class SchedulerFairnessPolicy" in source
    assert "class SchedulerResourceReservation" in source
    assert "json.dumps" not in source
    assert "json.loads" not in source
    assert "asyncio" not in source
