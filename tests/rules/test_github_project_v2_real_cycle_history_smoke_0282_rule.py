from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/context/"
    "github_project_v2_real_cycle_history_smoke_0282.py"
)
TOOL = (
    ROOT
    / "tools/"
    "run_github_project_v2_real_cycle_history_smoke_0282.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "GITHUB_PROJECT_V2_REAL_CYCLE_HISTORY_SMOKE_0282.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0282_R8_PROJECT_V2_REAL_CYCLE_HISTORY_SMOKE.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0282_R8_PROJECT_V2_REAL_CYCLE_HISTORY_SMOKE.md"
)
REPORT = (
    ROOT
    / "PHASE0282_R8_PROJECT_V2_REAL_CYCLE_HISTORY_SMOKE_REPORT.md"
)


def test_smoke_composes_existing_r4_r5_r6_contracts() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for required in (
        "GitHubProjectV2AppendOnlyCycleHistoryResult",
        "plan_github_project_v2_parent_sub_ticket_mutation",
        "plan_github_project_v2_theme_grouping_deployment",
        "adapter_reused",
        "exact_smoke_digest_required_for_execution",
    ):
        assert required in source
    assert source.count("@dataclass(frozen=True, slots=True)") == 2


def test_cli_reuses_r7_adapter_and_preview_is_default() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for required in (
        (
            "from tools."
            "apply_github_project_v2_operator_authorized_mutations_0282 "
            "import"
        ),
        "preview_is_default",
        "--confirm-smoke-digest",
        "--confirm-parent-plan-digest",
        "--confirm-theme-plan-digest",
        "partial_execution",
    ):
        assert required in source

    assert "if args.execute" in source
    assert (
        "args.confirm_smoke_digest != smoke.smoke_digest"
        in source
    )


def test_no_parallel_scheduler_transport_or_persistence_is_added() -> None:
    module = MODULE.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")

    for forbidden in (
        "LaboratoryManager",
        "Scheduler(",
        "EventBus(",
        "urlopen(",
        "requests.",
        "httpx.",
        "sqlite3",
        "psycopg",
        "qdrant_client",
    ):
        assert forbidden not in module
        assert forbidden not in tool


def test_phase_documents_controlled_real_boundary() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )
    for required in (
        "existing_r7_adapter_reused: true",
        "preview_is_default: true",
        "exact_smoke_digest_required_for_execution: true",
        "new_scheduler_added: false",
        "new_mutation_transport_added: false",
        "sql_write_added: false",
        "qdrant_write_added: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_closes_0282_and_names_next_series() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: controlled",
        "live_path_uses_real_backend: true",
        (
            "context_contract_version: "
            "missipy.github.project_v2_real_cycle_history_smoke.v1"
        ),
        "context_contract_changed: true",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0282_series_status: implementation_complete",
        "0283-qdrant-controlled-real-executor",
    ):
        assert required in report
