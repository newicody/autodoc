from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_operator_cli_remains_adapter_only() -> None:
    path = ROOT / "src" / "context" / "source_candidate_operator_cli.py"
    text = path.read_text(encoding="utf-8").lower()

    forbidden = (
        "sourcecandidatestorepolicy(",
        "upsert_source_candidate",
        "load_source_candidate_store",
        "eventtype.source_candidate",
        "scheduler(",
        "priorityqueue(",
        "requests",
        "qdrant",
        "openvino",
    )
    for token in forbidden:
        assert token not in text


def test_operator_cli_help_gate_documents_expected_commands() -> None:
    readme = ROOT / "doc" / "releases" / "README_PHASE6_12_SOURCE_CANDIDATE_OPERATOR_CLI_HELP.md"
    text = readme.read_text(encoding="utf-8")
    for command in ("intake", "review", "decide", "review-audit", "report", "report-file", "bundle"):
        assert command in text
