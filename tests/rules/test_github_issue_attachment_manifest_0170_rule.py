from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "github_issue_attachment_manifest.py"
TOOL = ROOT / "tools" / "build_github_issue_attachment_manifest.py"
BOOTSTRAP = ROOT / "tools" / "build_github_idea_repo_attachment_bootstrap_bundle.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_ISSUE_ATTACHMENT_MANIFEST_0170.md"
RULE = ROOT / "doc" / "code-rules" / "0170_github_issue_attachment_manifest_rule.md"


def test_0170_attachment_manifest_is_reference_only() -> None:
    text = MODULE.read_text(encoding="utf-8") + TOOL.read_text(encoding="utf-8") + BOOTSTRAP.read_text(encoding="utf-8")
    for token in [
        "no GitHub API call",
        "no remote mutation",
        "GitHub Actions artifacts remain the source system",
        "no user artifacts in Autodoc repository",
        "server dataset before conversion",
        "github_issue_attachment_reference",
    ]:
        assert token in text
    forbidden = ["requests.", "urllib.request", "subprocess.run(['git", 'subprocess.run(["git', "gh api", "workflow_dispatch"]
    for token in forbidden:
        assert token not in text


def test_0170_docs_lock_attachment_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "photo, audio, video, PDF, archive, and text",
        "GitHub issue attachment references only",
        "no GitHub API call",
        "no remote mutation",
        "GitHub Actions artifacts remain the source system",
        "no user artifacts in Autodoc repository",
        "server dataset before conversion",
    ]:
        assert token in doc
        assert token in rule
