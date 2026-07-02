from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_source_candidate_decision_has_scheduler_events() -> None:
    event_source = _read("src/contracts/event.py")
    assert "SOURCE_CANDIDATE_DECISION" in event_source
    assert "SOURCE_CANDIDATE_DECISION_RESULT" in event_source


def test_source_candidate_decision_has_handler_and_result_event() -> None:
    handlers = _read("src/context/source_candidate_decision_handlers.py")
    assert "class SourceCandidateDecisionHandler" in handlers
    assert "run_source_candidate_decision" in handlers
    assert "EventType.SOURCE_CANDIDATE_DECISION_RESULT" in handlers


def test_source_candidate_decision_cli_uses_scheduler_path() -> None:
    cli = _read("src/context/source_candidate_decision_cli.py")
    assert "Scheduler(" in cli
    assert "Dispatcher(" in cli
    assert "SourceCandidateDecisionHandler" in cli
    assert "EventType.SOURCE_CANDIDATE_DECISION" in cli
    assert "run_source_candidate_decision(" not in cli


def test_source_candidate_decision_does_not_add_external_backends() -> None:
    decision = _read("src/context/source_candidate_decision.py")
    forbidden = ("github", "requests", "qdrant", "openvino", "subprocess")
    lowered = decision.lower()
    for token in forbidden:
        assert token not in lowered
