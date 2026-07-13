from pathlib import Path
import hashlib


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_project_v2_append_only_cycle_history_0282.py"
GLOBAL_DOC = ROOT / "doc/architecture/GLOBAL_ARCHITECTURE_CURRENT_0282.md"
DEV_DOC = ROOT / "doc/architecture/PROJECTV2_CYCLE_HISTORY_DEVELOPMENT_0282.md"
COMPARE_DOC = ROOT / "doc/architecture/PROJECT_BEGINNING_CURRENT_COMPARISON_0282.md"
CURRENT = ROOT / "doc/architecture/CURRENT_ARCHITECTURE_STATE_0154.md"
LAYERS = ROOT / "doc/ARCHITECTURE_LAYERS.md"
README_CURRENT = ROOT / "doc/README_CURRENT.md"
OPERATIONAL_DOT = ROOT / "doc/docs/architecture/runtime/174_rebuilt_runtime_global_current_state.dot"
HERITAGE_DOT = ROOT / "doc/docs/architecture/00_global.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0282_R4_PROJECT_V2_APPEND_ONLY_CYCLE_HISTORY.md"
REPORT = ROOT / "PHASE0282_R4_PROJECT_V2_APPEND_ONLY_CYCLE_HISTORY_REPORT.md"

# Exact SHA-256 of the public heritage graph used as the r4 baseline.
HERITAGE_SHA256 = "65f279b7eb4e522e445e88749d55dd729bc17e9e964a9a8f873eaf084675070c"


def test_history_contract_is_immutable_and_composes_r2_r3() -> None:
    source = MODULE.read_text(encoding="utf-8")
    assert source.count("@dataclass(frozen=True, slots=True)") == 4
    for required in (
        "GitHubProjectV2CycleLineageResult",
        "GitHubProjectV2NormalizedParentThemeItem",
        "GitHubProjectV2CycleHistoryEntry",
        "GitHubProjectV2AppendOnlyCycleHistoryCommand",
        "GitHubProjectV2AppendOnlyCycleHistoryPolicy",
        "GitHubProjectV2AppendOnlyCycleHistoryResult",
        'action="append"',
        'action="replay"',
        'action = "collision"',
        "existing history entry digest mismatch",
    ):
        assert required in source


def test_history_contract_has_no_io_transport_or_scheduler_path() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for forbidden in (
        "argparse",
        "subprocess",
        "urllib.request",
        "requests",
        "httpx",
        "urlopen(",
        "open(",
        "write_text(",
        "sqlite3",
        "psycopg",
        "qdrant_client",
        "Scheduler(",
        "EventBus(",
    ):
        assert forbidden not in source
    for required in (
        '("append_only_projection", True)',
        '("external_call_performed", False)',
        '("graphql_mutation_allowed", False)',
        '("remote_mutation_allowed", False)',
        '("filesystem_write_allowed", False)',
        '("sql_write_allowed", False)',
        '("qdrant_write_allowed", False)',
        '("scheduler_modified", False)',
    ):
        assert required in source


def test_three_requested_architecture_views_exist_and_are_linked() -> None:
    global_text = GLOBAL_DOC.read_text(encoding="utf-8")
    dev_text = DEV_DOC.read_text(encoding="utf-8")
    compare_text = COMPARE_DOC.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    layers = LAYERS.read_text(encoding="utf-8")
    readme = README_CURRENT.read_text(encoding="utf-8")

    assert "architecture globale courante" in global_text
    assert "Schéma du développement en cours" in dev_text
    assert "orientation du début et architecture actuelle" in compare_text
    assert global_text.count("```mermaid") >= 1
    assert dev_text.count("```mermaid") >= 2
    assert compare_text.count("```mermaid") >= 2

    for filename in (
        GLOBAL_DOC.name,
        DEV_DOC.name,
        COMPARE_DOC.name,
    ):
        assert filename in current
        assert filename in layers
        assert filename in readme


def test_operational_dot_is_refreshed_but_heritage_is_unchanged() -> None:
    operational = OPERATIONAL_DOT.read_text(encoding="utf-8")
    assert "0282-r4 current operational architecture" in operational
    for required in (
        "ProjectV2 append-only cycle history",
        "0282-r3 parent/theme normalization",
        "0282-r2 cycle lineage contract",
        "existing-Scheduler fake laboratory",
        "SQL durable authority",
        "Observation only",
    ):
        assert required in operational

    actual = hashlib.sha256(HERITAGE_DOT.read_bytes()).hexdigest()
    assert actual == HERITAGE_SHA256


def test_docs_lock_boundaries_and_next_phase() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (GLOBAL_DOC, DEV_DOC, COMPARE_DOC, MANIFEST, REPORT)
    )
    for required in (
        "new_runtime_module_added: true",
        "new_cli_added: false",
        "new_adapter_added: false",
        "github_mutation_performed: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "heritage_global_graph_modified: false",
        "operational_global_graph_refreshed: true",
        "0282-r5-projectv2-parent-sub-ticket-mutation-plan",
    ):
        assert required in combined


def test_phase_report_versions_contract_and_code_rule_review() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "live_path_uses_real_backend: true",
        "context_contract_version: missipy.github.project_v2_cycle_history_projection.v1",
        "context_contract_changed: true",
        "search_commands_bounded: n/a",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
    ):
        assert required in report
