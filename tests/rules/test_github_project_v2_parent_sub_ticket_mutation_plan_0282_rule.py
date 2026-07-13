from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/context/"
    "github_project_v2_parent_sub_ticket_mutation_plan_0282.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "GITHUB_PROJECT_V2_PARENT_SUB_TICKET_MUTATION_PLAN_0282.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0282_R5_PROJECT_V2_PARENT_SUB_TICKET_MUTATION_PLAN.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0282_R5_PROJECT_V2_PARENT_SUB_TICKET_MUTATION_PLAN.md"
)
REPORT = (
    ROOT
    / "PHASE0282_R5_PROJECT_V2_PARENT_SUB_TICKET_MUTATION_PLAN_REPORT.md"
)


def test_plan_contract_is_immutable_and_reuses_r4_history() -> None:
    source = MODULE.read_text(encoding="utf-8")

    assert source.count("@dataclass(frozen=True, slots=True)") == 5
    for required in (
        "GitHubProjectV2AppendOnlyCycleHistoryResult",
        "GitHubProjectV2CycleHistoryEntry",
        "GitHubProjectV2IssueSnapshot",
        "GitHubProjectV2ParentSubTicketMutationCommand",
        "GitHubProjectV2ParentSubTicketMutationPolicy",
        "GitHubProjectV2ParentSubTicketMutationOperation",
        "GitHubProjectV2ParentSubTicketMutationPlan",
        "create_and_link",
        "link_existing",
        "replay",
        "collision",
        "MARKER_PREFIX",
    ):
        assert required in source


def test_plan_adds_no_transport_adapter_or_mutation() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for forbidden in (
        "argparse",
        "subprocess",
        "urllib.request",
        "requests",
        "httpx",
        "urlopen(",
        "graphql(",
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
        '("github_mutation_allowed", False)',
        '("github_mutation_performed", False)',
        '("filesystem_write_allowed", False)',
        '("sql_write_allowed", False)',
        '("qdrant_write_allowed", False)',
        '("scheduler_modified", False)',
    ):
        assert required in source


def test_documentation_locks_plan_only_scope() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "r4_history_reused: true",
        "existing_idempotency_pattern_reused: true",
        "new_runtime_module_added: true",
        "new_cli_added: false",
        "new_adapter_added: false",
        "graphql_query_added: false",
        "graphql_mutation_added: false",
        "github_mutation_performed: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_versions_contract_and_points_to_r6() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "live_path_uses_real_backend: n/a",
        (
            "context_contract_version: "
            "missipy.github.project_v2_parent_sub_ticket_mutation_plan.v1"
        ),
        "context_contract_changed: true",
        "search_commands_bounded: n/a",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0282-r6-projectv2-theme-grouping-deployment-plan",
    ):
        assert required in report
