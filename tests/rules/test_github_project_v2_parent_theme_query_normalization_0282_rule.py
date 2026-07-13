from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = (
    ROOT
    / "src/context/github_project_v2_query_only_snapshot_0272.py"
)
MODULE = (
    ROOT
    / "src/context/"
    "github_project_v2_parent_theme_query_normalization_0282.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "GITHUB_PROJECT_V2_PARENT_THEME_QUERY_NORMALIZATION_0282.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0282_R3_PROJECT_V2_PARENT_THEME_QUERY_NORMALIZATION.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0282_R3_PROJECT_V2_PARENT_THEME_QUERY_NORMALIZATION.md"
)
REPORT = (
    ROOT
    / "PHASE0282_R3_PROJECT_V2_PARENT_THEME_QUERY_NORMALIZATION_REPORT.md"
)


def test_existing_query_is_extended_not_replaced() -> None:
    source = SNAPSHOT.read_text(encoding="utf-8")

    assert source.count("ITEMS_QUERY =") == 1
    assert "parent {" in source
    assert "subIssues(first: 100)" in source
    assert "pageInfo { hasNextPage endCursor }" in source
    assert "mutation AutodocProjectV2Items" not in source


def test_normalizer_reuses_r2_reference_builders() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for required in (
        "build_github_project_v2_issue_ref",
        "build_github_project_v2_item_ref",
        "build_github_project_v2_theme_ref",
        "build_ticket_revision_id",
        "SNAPSHOT_SCHEMA",
    ):
        assert required in source

    assert source.count("@dataclass(frozen=True, slots=True)") == 4


def test_normalizer_adds_no_transport_mutation_or_persistence() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for forbidden in (
        "argparse",
        "subprocess",
        "urllib.request",
        "requests",
        "httpx",
        "urlopen(",
        "sqlite3",
        "psycopg",
        "qdrant_client",
        "Scheduler(",
        "EventBus(",
    ):
        assert forbidden not in source

    for required in (
        '("external_call_performed", False)',
        '("graphql_query_performed", False)',
        '("graphql_mutation_allowed", False)',
        '("remote_mutation_allowed", False)',
        '("sql_write_allowed", False)',
        '("qdrant_write_allowed", False)',
        '("scheduler_modified", False)',
    ):
        assert required in source


def test_phase_documents_live_query_extension_and_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "existing_query_extended: true",
        "parallel_query_transport_added: false",
        "new_runtime_module_added: true",
        "new_cli_added: false",
        "new_adapter_added: false",
        "github_api_client_added: false",
        "graphql_mutation_added: false",
        "github_mutation_performed: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_phase_report_versions_contract_and_next_projection() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "live_path_uses_real_backend: true",
        (
            "context_contract_version: "
            "missipy.github.project_v2_parent_theme_normalization.v1"
        ),
        "context_contract_changed: true",
        "search_commands_bounded: n/a",
        "network_added: false",
        "github_api_added: false",
        "github_api_query_extended: true",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0282-r4-projectv2-append-only-cycle-history-projection",
    ):
        assert required in report
