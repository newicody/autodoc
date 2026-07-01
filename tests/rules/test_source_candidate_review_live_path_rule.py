
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_source_candidate_review_declares_kernel_events() -> None:
    text = _read("src/contracts/event.py")
    assert "SOURCE_CANDIDATE_REVIEW" in text
    assert "SOURCE_CANDIDATE_REVIEW_RESULT" in text


def test_source_candidate_review_has_live_path_handler() -> None:
    text = _read("src/context/source_candidate_handlers.py")
    assert "class SourceCandidateReviewHandler" in text
    assert "run_source_candidate_review" in text
    assert "SOURCE_CANDIDATE_REVIEW_RESULT" in text


def test_source_candidate_review_cli_is_scheduler_adapter_not_store_adapter() -> None:
    text = _read("src/context/source_candidate_review_cli.py")
    assert "SourceCandidateReviewCommand" in text
    assert "Scheduler(" in text
    assert "EventType.SOURCE_CANDIDATE_REVIEW" in text
    assert "load_source_candidate_store" not in text
    assert "upsert_source_candidate" not in text
    assert "write_source_candidate_store" not in text
