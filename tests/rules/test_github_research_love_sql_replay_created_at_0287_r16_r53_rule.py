from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/github_research_love_sql_persistence_0287.py"
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_SQL_REPLAY_CREATED_AT_0287_R16_R53.md"
RULE = ROOT / "doc/code-rules/0287_r16_r53_sql_replay_created_at_rule.md"


def test_r16_r53_preserves_sql_authority_and_exact_immutability() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    documentation = ARCHITECTURE.read_text(encoding="utf-8") + RULE.read_text(
        encoding="utf-8"
    )

    assert "_resolve_persistence_created_at" in source
    assert "existing immutable analysis entities disagree on created_at" in source
    assert "existing_mapping() == expected_mapping()" in source
    assert "PostgreSQL" in documentation
    assert "autorité durable" in documentation
    assert "Qdrant" in documentation
    assert "file JSONL" in documentation
    assert "second Scheduler" in documentation


def test_r16_r53_does_not_add_process_or_scheduler_authority() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    forbidden = (
        "subprocess",
        "multiprocessing",
        "threading",
        "Scheduler(",
        "Dispatcher(",
    )
    for token in forbidden:
        assert token not in source
