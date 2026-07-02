from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_source_candidate_decision_audit_is_local_and_stdlib_only() -> None:
    decision = _read("src/context/source_candidate_decision.py")
    assert "SourceCandidateDecisionAuditPolicy" in decision
    assert "write_source_candidate_decision_audit" in decision
    assert "NamedTemporaryFile" in decision
    forbidden = ("requests", "qdrant", "openvino", "subprocess")
    lowered = decision.lower()
    for token in forbidden:
        assert token not in lowered


def test_source_candidate_decision_cli_exposes_audit_as_scheduler_command_field() -> None:
    cli = _read("src/context/source_candidate_decision_cli.py")
    assert "--audit-file" in cli
    assert "--audit-without-candidates" in cli
    assert "SourceCandidateDecisionAuditPolicy" in cli
    assert "Scheduler(" in cli
