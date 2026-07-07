from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_github_actions_artifact_fetch_once.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_ACTIONS_ARTIFACT_FETCH_ONCE_0168.md"
RULE = ROOT / "doc" / "code-rules" / "0168_github_actions_artifact_fetch_once_rule.md"


def test_0168_fetch_tool_locks_read_only_dataset_boundary() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for token in [
        "read-only GitHub Actions artifact fetch",
        "uses configured server dataset",
        "calls 0167 server dataset sync",
        "no conversion before complete sync",
        "no remote mutation",
    ]:
        assert token in text

    forbidden = ["requests.post", "requests.patch", "requests.delete", "method=\"POST\"", "method=\"PATCH\"", "method=\"DELETE\""]
    lowered = text.lower()
    for token in forbidden:
        assert token.lower() not in lowered


def test_0168_docs_lock_fetch_after_github_actions_and_before_conversion() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "read-only GitHub Actions artifact fetch",
        "GitHub Actions artifacts remain the source system",
        "server dataset configured by 0167",
        "conversion starts only after raw sync",
        "VisPy observes the sync result",
        "does not publish GitHub results",
    ]:
        assert token in doc
        assert token in rule
