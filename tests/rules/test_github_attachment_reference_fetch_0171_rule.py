from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "GITHUB_ATTACHMENT_REFERENCE_FETCH_0171.md"
RULE = ROOT / "doc" / "code-rules" / "0171_github_attachment_reference_fetch_rule.md"
TOOL = ROOT / "tools" / "run_github_attachment_reference_fetch_once.py"
CONTRACT = ROOT / "src" / "context" / "github_attachment_reference_fetch.py"


def test_0171_docs_lock_attachment_fetch_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "GitHub issue attachment references only",
        "configured server dataset",
        "conversion is queued only after attachment fetch completes",
        "no user artifacts in Autodoc repository",
        "no remote mutation",
        "VisPy observation event",
    ]:
        assert token in doc
        assert token in rule


def test_0171_context_has_no_network_client() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    assert "urllib" not in text
    assert "requests" not in text
    assert "urlopen" not in text
    assert "GitHubAttachmentReferenceFetchReport" in text


def test_0171_tool_requires_explicit_network_opt_in() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert "--allow-network" in text
    assert "network fetch disabled" in text
    assert "allow_remote_mutation" not in text
    assert "sql" not in text.lower()
    assert "qdrant" not in text.lower()
