from __future__ import annotations

from pathlib import Path


_OPERATOR_CLI = Path("src/context/source_candidate_operator_cli.py")


def test_source_candidate_operator_cli_is_adapter_only() -> None:
    text = _OPERATOR_CLI.read_text(encoding="utf-8")
    forbidden = (
        "Scheduler(",
        "Dispatcher(",
        "PriorityQueue(",
        "SourceCandidateStorePolicy",
        "load_source_candidate_store",
        "write_source_candidate",
        "requests",
        "qdrant",
        "openvino",
    )
    lowered = text.lower()
    for token in forbidden:
        assert token.lower() not in lowered


def test_source_candidate_operator_cli_exposes_existing_operator_commands() -> None:
    text = _OPERATOR_CLI.read_text(encoding="utf-8")
    for command in (
        "intake",
        "review",
        "decide",
        "review-audit",
        "report",
        "report-file",
        "bundle",
    ):
        assert f'"{command}"' in text
