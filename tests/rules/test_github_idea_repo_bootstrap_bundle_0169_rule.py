from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "build_github_idea_repo_bootstrap_bundle.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_IDEA_REPO_BOOTSTRAP_BUNDLE_0169.md"
RULE = ROOT / "doc" / "code-rules" / "0169_github_idea_repo_bootstrap_bundle_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0169_CHANGED_FILES.md"


def test_0169_bootstrap_rule_locks_local_only_boundary() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for token in [
        "reuse 0166 templates",
        "local bootstrap only",
        "remote_mutation_performed",
        "github_api_called",
        "newicody/autodoc-ideas",
        "development_repository_rejected",
    ]:
        assert token in text

    for forbidden in ["urllib.request", "requests.", "gh api", "git push", "workflow_dispatch"]:
        assert forbidden not in text


def test_0169_docs_describe_external_repo_bootstrap() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "external idea repository",
        "reuse 0166 templates",
        "no GitHub API call",
        "no remote mutation",
        "GitHub Actions artifacts remain the source system",
        "no user artifacts in Autodoc repository",
    ]:
        assert token in doc
        assert token in rule


def test_0169_manifest_lists_expected_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/build_github_idea_repo_bootstrap_bundle.py",
        "tests/tools/test_github_idea_repo_bootstrap_bundle_0169.py",
        "tests/rules/test_github_idea_repo_bootstrap_bundle_0169_rule.py",
        "doc/architecture/GITHUB_IDEA_REPO_BOOTSTRAP_BUNDLE_0169.md",
    ]:
        assert token in manifest
