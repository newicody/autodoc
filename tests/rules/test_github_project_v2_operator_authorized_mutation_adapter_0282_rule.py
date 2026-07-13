from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/apply_github_project_v2_operator_authorized_mutations_0282.py"
EXISTING = ROOT / "tools/publish_github_advisory_issue_comment_0281.py"
ARCH = ROOT / "doc/architecture/GITHUB_PROJECT_V2_OPERATOR_AUTHORIZED_MUTATION_ADAPTER_0282.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0282_R7_PROJECT_V2_OPERATOR_AUTHORIZED_MUTATION_ADAPTER.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0282_R7_PROJECT_V2_OPERATOR_AUTHORIZED_MUTATION_ADAPTER.md"
REPORT = ROOT / "PHASE0282_R7_PROJECT_V2_OPERATOR_AUTHORIZED_MUTATION_ADAPTER_REPORT.md"


def test_adapter_reuses_existing_gh_cli_boundary():
    existing = EXISTING.read_text(encoding="utf-8")
    source = TOOL.read_text(encoding="utf-8")
    assert "subprocess" in existing
    assert "gh" in existing
    assert "subprocess.run" in source
    assert "urlopen" not in source
    assert "requests" not in source
    assert "httpx" not in source


def test_adapter_has_double_operator_gate_and_preview_default():
    source = TOOL.read_text(encoding="utf-8")
    for required in (
        'choices=("approve",)',
        '"--execute"',
        '"--confirm-parent-plan-digest"',
        '"--confirm-theme-plan-digest"',
        '"preview_is_default": True',
        '"view_grouping_automated": False',
    ):
        assert required in source


def test_adapter_supports_only_planned_mutations():
    source = TOOL.read_text(encoding="utf-8")
    for required in (
        "AddSubIssueInput!",
        "UpdateProjectV2FieldInput!",
        "UpdateProjectV2ItemFieldValueInput!",
        "repos/{repository}/issues",
        "X-GitHub-Api-Version",
    ):
        assert required in source
    for forbidden in (
        "removeSubIssue",
        "deleteProjectV2",
        "deleteIssue",
        "Scheduler(",
        "EventBus(",
        "sqlite3",
        "qdrant_client",
    ):
        assert forbidden not in source


def test_phase_documents_real_adapter_boundaries():
    combined = "\n".join(p.read_text(encoding="utf-8") for p in (ARCH, MANIFEST, CHANGELOG, REPORT))
    for required in (
        "existing_gh_cli_boundary_reused: true",
        "preview_is_default: true",
        "exact_plan_digest_confirmation_required: true",
        "new_cli_added: true",
        "new_adapter_added: true",
        "network_added: true",
        "github_api_added: true",
        "view_grouping_automated: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_names_real_backend_and_r8():
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: real",
        "live_path_uses_real_backend: true",
        "context_contract_version: n/a",
        "context_contract_changed: false",
        "github_mutation_performed_during_tests: false",
        "0282-r8-projectv2-real-cycle-history-smoke",
    ):
        assert required in report
