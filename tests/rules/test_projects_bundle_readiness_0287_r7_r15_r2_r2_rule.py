from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "templates/github/projects-repository/scripts/projects_bundle_readiness_contract.py"
CLI = ROOT / "templates/github/projects-repository/scripts/check_projects_bundle_readiness.py"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
TEST = ROOT / "tests/tools/test_projects_bundle_readiness_0287_r7_r15_r2_r2.py"
REPORT = ROOT / "PHASE0287_R7_R15_R2_R2_PROJECTS_VIEWS_ACTIONS_READINESS_REPAIR_REPORT.md"
ARCH = ROOT / "doc/architecture/PROJECTS_VIEWS_ACTIONS_READINESS_REPAIR_0287_R7_R15_R2_R2.md"
DOT = ROOT / "doc/architecture/PROJECTS_VIEWS_ACTIONS_READINESS_REPAIR_0287_R7_R15_R2_R2.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R15_R2_R2_PROJECTS_VIEWS_ACTIONS_READINESS_REPAIR.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R15_R2_R2_PROJECTS_VIEWS_ACTIONS_READINESS_REPAIR.md"
RULE_TEST = Path(__file__)


def test_patch_bundle_is_complete_and_dot_is_source_only() -> None:
    for path in (
        CONTRACT,
        CLI,
        INSTALLATION,
        TEST,
        REPORT,
        ARCH,
        DOT,
        CHANGELOG,
        MANIFEST,
        RULE_TEST,
    ):
        assert path.is_file(), path
    assert not DOT.with_suffix(".svg").exists()


def test_contract_checks_existing_view_configuration_not_only_names() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    for required in (
        "class ViewReadiness",
        "expected_layout",
        "expected_filter",
        "expected_visible_fields",
        "expected_column_field",
        "expected_row_group_field",
        "view name is not unique",
        "visible fields or their order differ",
        "vertical group field differs",
    ):
        assert required in text


def test_actions_and_copilot_readiness_are_separate() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    for required in (
        "class ActionsPolicy",
        "blocked_actions",
        "unpinned_actions",
        "authoritative_ready",
        "copilot_ready",
        "Copilot advisory is explicitly disabled",
        "workflow is manual-dispatch only",
    ):
        assert required in text


def test_cli_is_query_only_and_has_no_execute_or_mutation_surface() -> None:
    text = CLI.read_text(encoding="utf-8")
    for required in (
        "_PROJECT_QUERY",
        "groupByFields",
        "verticalGroupByFields",
        "actions/permissions/selected-actions",
        "AUTODOC_COPILOT_ADVISORY_ENABLED",
        "remote_mutation_allowed",
    ):
        assert required in text
    for forbidden in (
        'parser.add_argument("--execute"',
        '"--method", "POST"',
        '"--method", "PUT"',
        "createProjectV2",
        "updateProjectV2",
        "addProjectV2ItemById",
    ):
        assert forbidden not in text


def test_installation_uses_real_preview_digest_and_readiness_command() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    for required in (
        "/tmp/projectv2-configuration-preview.json",
        "jq -r '.plan_digest // empty'",
        '--confirm-plan-digest "$PLAN_DIGEST"',
        "check_projects_bundle_readiness.py",
        "projectv2_exact",
        "authoritative_ready",
        "copilot_ready",
        "manual_dispatch_only",
        "github_owned_allowed",
    ):
        assert required in text
    legacy_heading = "### Compatibilité des anciens exemples — ne pas exécuter"
    assert legacy_heading in text
    safe_command = '--confirm-plan-digest "$PLAN_DIGEST"'
    legacy_placeholder = "--confirm-plan-digest '<PLAN_DIGEST>'"
    legacy_empty = "--confirm-plan-digest ''"
    assert text.index(safe_command) < text.index(legacy_heading)
    assert text.count(legacy_placeholder) == 1
    assert text.count(legacy_empty) == 1
    assert text.index(legacy_heading) < text.index(legacy_placeholder)
    assert text.index(legacy_heading) < text.index(legacy_empty)


def test_report_contains_mandatory_code_rule_review_fields() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "live_path_uses_real_backend: false",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: true",
        "github_api_added: true",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "search_commands_bounded: n/a",
    ):
        assert required in text
