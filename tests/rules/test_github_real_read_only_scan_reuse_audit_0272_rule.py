from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src/context/github_real_read_only_scan_reuse_audit_0272.py"
TOOL = ROOT / "tools/audit_github_real_read_only_scan_reuse_0272.py"
DOC = ROOT / "doc/architecture/GITHUB_REAL_READ_ONLY_SCAN_REUSE_AUDIT_0272.md"
REPORT = ROOT / "PHASE0272_GITHUB_REAL_READ_ONLY_SCAN_REUSE_AUDIT_TEST_REPORT.md"


def test_0272_audit_has_no_network_or_mutation_backend() -> None:
    combined = CORE.read_text(encoding="utf-8") + TOOL.read_text(encoding="utf-8")
    for forbidden in (
        "urllib.request",
        "requests",
        "httpx",
        "PyGithub",
        "create_issue(",
        "update_issue(",
        "subprocess",
        "Scheduler.run(",
        "RuntimeManager",
    ):
        assert forbidden not in combined


def test_0272_documents_reuse_before_new_module() -> None:
    text = DOC.read_text(encoding="utf-8")
    for phrase in (
        "GitHubActionsClient",
        "token_env",
        "allowed_repositories",
        "0267",
        "remote mutation gate",
        "issue scan client is absent",
    ):
        assert phrase in text


def test_0272_phase_report_contains_required_review_block() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for phrase in (
        "code_rule_review: done",
        "live_path_status: n/a",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: false",
        "github_api_added: false",
        "search_commands_bounded: true",
    ):
        assert phrase in text
