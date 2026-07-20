from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/runtime/controlproxy_scheduler_adapter.py"
ARCHITECTURE = (
    ROOT
    / "doc/architecture/CONTROLPROXY_SCHEDULER_ADAPTER_0287_R16_R43.md"
)
RULE = (
    ROOT
    / "doc/code-rules/0287_r16_r43_controlproxy_scheduler_adapter_rule.md"
)


def test_r16_r52_replay_ignores_only_initial_materialization_timestamp() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert '_CONTROLFS_REPLAY_VOLATILE_FIELDS = frozenset({"created_at"})' in source
    assert "_manifest_replay_mapping" in source
    assert "differing_fields" in source
    assert "payload.pop(field, None)" in source
    assert "actual_replay != expected_replay" in source


def test_r16_r52_documents_first_materialization_and_fail_closed_collision() -> None:
    combined = ARCHITECTURE.read_text(encoding="utf-8") + "\n" + RULE.read_text(
        encoding="utf-8"
    )

    assert "première matérialisation" in combined
    assert "created_at" in combined
    assert "TTL" in combined
    assert "Toute autre collision échoue fermée" in combined
    assert "PostgreSQL" in combined
    assert "file JSONL" in combined
