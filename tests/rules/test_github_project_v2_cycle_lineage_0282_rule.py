from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/context/github_project_v2_cycle_lineage_0282.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "GITHUB_PROJECT_V2_CYCLE_LINEAGE_CONTRACT_0282.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0282_R2_PROJECT_V2_CYCLE_LINEAGE_CONTRACT.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0282_R2_PROJECT_V2_CYCLE_LINEAGE_CONTRACT.md"
)
REPORT = (
    ROOT
    / "PHASE0282_R2_PROJECT_V2_CYCLE_LINEAGE_CONTRACT_REPORT.md"
)


def test_contract_is_immutable_serializable_and_policy_driven() -> None:
    source = MODULE.read_text(encoding="utf-8")

    assert source.count("@dataclass(frozen=True, slots=True)") == 3
    for required in (
        "GitHubProjectV2CycleLineageCommand",
        "GitHubProjectV2CycleLineagePolicy",
        "GitHubProjectV2CycleLineageResult",
        "def to_json_dict",
        "def to_summary",
        "build_origin_frame_id",
        "require_parent_after_initial",
        "require_previous_cycle_after_initial",
        "max_cycle_ordinal",
        "max_sub_issue_refs",
        "max_theme_refs",
    ):
        assert required in source


def test_contract_has_no_transport_persistence_or_scheduler_path() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for forbidden in (
        "argparse",
        "subprocess",
        "urllib.request",
        "requests",
        "httpx",
        "graphql(",
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


def test_r2_documents_new_module_justification_and_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "reuse_audit_completed: true",
        "existing_suitable_module_found: false",
        "new_runtime_module_added: true",
        "new_cli_added: false",
        "new_adapter_added: false",
        "github_api_added: false",
        "graphql_mutation_added: false",
        "github_mutation_performed: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_phase_report_versions_the_new_contract_explicitly() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "live_path_uses_real_backend: n/a",
        (
            "context_contract_version: "
            "missipy.github.project_v2_cycle_lineage.v1"
        ),
        "context_contract_changed: true",
        "search_commands_bounded: n/a",
        "network_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
    ):
        assert required in report


def test_next_phase_is_query_only_normalization() -> None:
    report = REPORT.read_text(encoding="utf-8")
    assert (
        "0282-r3-projectv2-parent-theme-query-normalization"
        in report
    )
