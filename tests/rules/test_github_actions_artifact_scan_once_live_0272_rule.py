from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src/context/github_actions_artifact_scan_once_live_0272.py"
TOOL = ROOT / "tools/run_github_actions_artifact_scan_once_live_0272.py"
DOC = ROOT / "doc/architecture/GITHUB_ACTIONS_ARTIFACT_SCAN_ONCE_LIVE_0272.md"
RULE = ROOT / "doc/code-rules/0272_github_actions_artifact_scan_once_live_rule.md"
PROJECT_CONFIG = ROOT / "config/github_project_push_frame.example.ini"
WORKFLOW = ROOT / "templates/github/autodoc-ticket-artifact.yml"


def test_0272_r2_reuses_existing_artifact_fetch_without_issue_api() -> None:
    combined = CORE.read_text(encoding="utf-8") + TOOL.read_text(encoding="utf-8")
    assert "tools/run_github_actions_artifact_fetch_once.py" in combined
    assert "direct_issue_scan_required" in combined
    for forbidden in (
        "/issues?",
        "list_repository_issues",
        "GitHubIssuesReadOnlyClient",
        "create_issue(",
        "update_issue(",
        "workflow_dispatch",
        "Scheduler" + ".run(",
        "Runtime" + "Manager",
    ):
        if forbidden == "workflow_dispatch":
            continue
        assert forbidden not in combined


def test_0272_r2_keeps_mutation_and_secret_boundaries() -> None:
    combined = CORE.read_text(encoding="utf-8") + TOOL.read_text(encoding="utf-8")
    for phrase in (
        '"remote_mutation_allowed": False',
        '"token_value_serialized": False',
        '"sql_write_allowed": False',
        '"qdrant_write_allowed": False',
    ):
        assert phrase in combined
    assert "Authorization" not in CORE.read_text(encoding="utf-8")


def test_0272_r2_aligns_example_config_and_workflow() -> None:
    config = PROJECT_CONFIG.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "scan_command = tools/run_github_actions_artifact_scan_once_live_0272.py" in config
    assert "--execute --policy-decision-id policy:0272:fcron-actions-artifacts-read-only" in config
    assert "allow_workflow_dispatch = false" in config
    assert "workflow_dispatch:" not in workflow


def test_0272_r2_documents_actions_artifact_path() -> None:
    combined = DOC.read_text(encoding="utf-8") + RULE.read_text(encoding="utf-8")
    for phrase in (
        "GitHub Action",
        "GitHub Actions artifacts",
        "run_github_actions_artifact_fetch_once.py",
        "direct issue scan",
        "remote mutation",
        "append-only",
    ):
        assert phrase in combined
