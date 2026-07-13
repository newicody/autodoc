from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_PROJECT_V2_CYCLE_HISTORY_REUSE_AUDIT_0282.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0282_R1_PROJECT_V2_CYCLE_HISTORY_REUSE_AUDIT.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0282_R1_PROJECT_V2_CYCLE_HISTORY_REUSE_AUDIT.md"
REPORT = ROOT / "PHASE0282_R1_PROJECT_V2_CYCLE_HISTORY_REUSE_AUDIT_REPORT.md"

REUSED = {
    "src/context/github_project_v2_query_only_snapshot_0272.py": (
        "DraftIssue", "fieldValues", "query_only", "graphql_mutation_allowed",
    ),
    "src/context/github_project_v2_snapshot_change_detection_0272.py": (
        "status_transition_count", "changed_paths", "local_snapshot_comparison_only",
    ),
    "src/context/github_project_v2_change_handoff_0272.py": ("SourceCandidate",),
    "src/context/github_project_v2_en_cours_dispatch_0275_r8.py": (
        "en_cours", "workflow_dispatch",
    ),
    "src/context/github_project_push_frame.py": ("History is append-only",),
    "src/context/github_project_scenario.py": ("project scenario",),
    "src/context/github_action_ticket_artifact.py": ("ticket artifact",),
}


def test_reuse_audit_names_existing_surfaces_and_markers() -> None:
    audit = ARCHITECTURE.read_text(encoding="utf-8")
    for relative, markers in REUSED.items():
        path = ROOT / relative
        assert path.is_file(), relative
        source = path.read_text(encoding="utf-8")
        assert relative.split("/")[-1] in audit
        for marker in markers:
            assert marker in source


def test_audit_selects_native_lineage_and_theme_projection() -> None:
    audit = ARCHITECTURE.read_text(encoding="utf-8")
    for required in (
        "native sub-issues",
        "cycle lineage",
        "Project field",
        "theme grouping",
        "cycle_ref",
        "previous_cycle_ref",
        "root_issue_ref",
        "parent_issue_ref",
        "sub_issue_refs",
        "theme_refs",
        "project_item_ref",
        "status_revision_ref",
        "result_issue_ref",
    ):
        assert required in audit


def test_audit_defers_runtime_and_remote_mutation() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )
    for required in (
        "runtime_source_modified: false",
        "new_runtime_module_added: false",
        "new_cli_added: false",
        "new_adapter_added: false",
        "graphql_mutation_added: false",
        "github_mutation_performed: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_next_phase_is_contract_first() -> None:
    report = REPORT.read_text(encoding="utf-8")
    audit = ARCHITECTURE.read_text(encoding="utf-8")
    assert "0282-r2-projectv2-cycle-lineage-contract" in report
    assert "pure immutable command/policy/result contract" in report
    assert "0282-r2  immutable local cycle-lineage contract" in audit
    assert "0282-r7  explicit operator-authorized adapter" in audit


def test_phase_report_contains_code_rule_review() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "live_path_uses_real_backend: n/a",
        "context_contract_version: n/a",
        "context_contract_changed: false",
        "search_commands_bounded: n/a",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
    ):
        assert required in report
