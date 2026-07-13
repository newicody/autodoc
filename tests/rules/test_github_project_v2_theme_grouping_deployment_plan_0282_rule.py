from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/context/"
    "github_project_v2_theme_grouping_deployment_plan_0282.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "GITHUB_PROJECT_V2_THEME_GROUPING_DEPLOYMENT_PLAN_0282.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0282_R6_PROJECT_V2_THEME_GROUPING_DEPLOYMENT_PLAN.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0282_R6_PROJECT_V2_THEME_GROUPING_DEPLOYMENT_PLAN.md"
)
REPORT = (
    ROOT
    / "PHASE0282_R6_PROJECT_V2_THEME_GROUPING_DEPLOYMENT_PLAN_REPORT.md"
)


def test_plan_is_immutable_and_reuses_r2_theme_refs() -> None:
    source = MODULE.read_text(encoding="utf-8")
    assert source.count("@dataclass(frozen=True, slots=True)") == 9
    assert "build_github_project_v2_theme_ref" in source
    assert "GITHUB_REST_API_VERSION = \"2026-03-10\"" in source


def test_plan_has_no_transport_execution_surface() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for forbidden in (
        "urlopen(",
        "requests.",
        "httpx.",
        "subprocess.",
        "graphql_client",
        "github_client",
        "sqlite3",
        "psycopg",
        "qdrant_client",
        "Scheduler(",
    ):
        assert forbidden not in source

    for required in (
        '("external_call_performed", False)',
        '("rest_mutation_allowed", False)',
        '("graphql_mutation_allowed", False)',
        '("github_mutation_performed", False)',
        '("view_mutation_automated", False)',
    ):
        assert required in source


def test_documents_field_assignment_and_manual_view_stages() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )
    for required in (
        "field_stage_planned: true",
        "assignment_stage_planned: true",
        "view_grouping_stage_planned: true",
        "view_grouping_automated: false",
        "new_cli_added: false",
        "new_adapter_added: false",
        "github_mutation_performed: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_versions_contract_and_names_r7() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "live_path_uses_real_backend: n/a",
        (
            "context_contract_version: "
            "missipy.github.project_v2_theme_grouping_deployment_plan.v1"
        ),
        "context_contract_changed: true",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0282-r7-projectv2-operator-authorized-mutation-adapter",
    ):
        assert required in report
