from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_CANONICAL_CONTINUATION_0287_R16_R34_R35.md"
RULE = ROOT / "doc/code-rules/0287_r16_r34_r35_scheduler_canonical_continuation_rule.md"
SOURCE = ROOT / "src/kernel/scheduler_canonical_continuation.py"


def test_r16_r34_r35_lock_grouped_canonical_scheduler_boundary() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")

    for token in (
        "relire PostgreSQL",
        "tick borné du Scheduler canonique déjà actif",
        "PostgreSQL reste l’autorité durable",
        "aucune file JSON ou JSONL",
        "VisPy reste observation-only",
    ):
        assert token in architecture

    for token in (
        "Exiger un Scheduler canonique déjà actif",
        "Borner chaque tick",
        "ne pas ajouter de manager, daemon",
        "Refuser une étape qui ne fait pas avancer durablement",
    ):
        assert token in rule

    assert "for _step_index in range(bound.max_task_steps)" in source
    assert "while True" not in source
    assert "Dispatcher(" not in source
    assert "EventBus(" not in source
    assert "json.dumps" not in source
    assert "json.loads" not in source
