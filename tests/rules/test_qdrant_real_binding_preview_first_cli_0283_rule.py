from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_qdrant_real_binding_0283.py"
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "QDRANT_REAL_BINDING_PREVIEW_FIRST_CLI_0283.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0283_R7_QDRANT_REAL_BINDING_PREVIEW_FIRST_CLI.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0283_R7_QDRANT_REAL_BINDING_PREVIEW_FIRST_CLI.md"
)
REPORT = (
    ROOT
    / "PHASE0283_R7_QDRANT_REAL_BINDING_PREVIEW_FIRST_CLI_REPORT.md"
)


def test_cli_reuses_r2_r4_r5_r6_surfaces() -> None:
    source = TOOL.read_text(encoding="utf-8")

    for required in (
        "build_qdrant_real_binding_configuration",
        "inspect_qdrant_real_binding_readiness",
        "run_qdrant_controlled_scheduler_projection_binding",
        "run_qdrant_controlled_scheduler_recall_binding",
        "derive_sqlite_authority_scope",
        "DbApiSqlContextStore",
    ):
        assert required in source


def test_cli_has_distinct_preview_live_and_effect_gates() -> None:
    source = TOOL.read_text(encoding="utf-8")

    for required in (
        '"--execute"',
        '"--live-readiness"',
        '"--authorize-projection"',
        '"--authorize-recall"',
        "--execute requires --live-readiness",
        "projection execute requires --authorize-projection",
        "recall execute requires --authorize-recall",
        "authorization flags require --execute",
        "is not operationally ready",
    ):
        assert required in source


def test_cli_does_not_add_parallel_runtime_or_admin_effects() -> None:
    source = TOOL.read_text(encoding="utf-8")

    for forbidden in (
        ".create_collection(",
        ".recreate_collection(",
        ".update_collection(",
        ".delete_collection(",
        "class Scheduler",
        "Scheduler(",
        "ControlProxy(",
        "EventBus(",
        "SharedMemory(",
        "memfd_create(",
        "mmap(",
        "subprocess.",
    ):
        assert forbidden not in source

    for required in (
        '"collection_created": False',
        '"collection_updated": False',
        '"collection_deleted": False',
        '"qdrant_started": False',
        '"scheduler_modified": False',
        '"new_scheduler_added": False',
        '"new_qdrant_executor_added": False',
        '"new_transport_added": False',
        '"control_proxy_integrated": False',
        '"event_bus_integrated": False',
        '"shm_or_mmio_integrated": False',
    ):
        assert required in source


def test_sql_recall_store_is_opened_read_only() -> None:
    source = TOOL.read_text(encoding="utf-8")

    assert 'resolved.as_uri() + "?mode=ro"' in source
    assert "uri=True" in source
    assert "auto_commit=False" in source
    assert "SQL authority database not found" in source


def test_phase_documents_architecture_and_scope() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "architecture_preserved: true",
        "preview_first: true",
        "live_readiness_is_explicit: true",
        "operation_authorization_is_explicit: true",
        "projection_authorization_separate: true",
        "recall_authorization_separate: true",
        "existing_r2_configuration_reused: true",
        "existing_r4_projection_binding_reused: true",
        "existing_r5_recall_binding_reused: true",
        "existing_r6_readiness_reused: true",
        "collection_created: false",
        "collection_updated: false",
        "collection_deleted: false",
        "scheduler_modified: false",
        "new_qdrant_executor_added: false",
        "new_transport_added: false",
        "control_proxy_integrated: false",
        "event_bus_integrated: false",
        "shm_or_mmio_integrated: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_versions_contract_and_names_r8() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "live_path_uses_real_backend: true",
        (
            "context_contract_version: "
            "missipy.qdrant.real_binding_preview_first_cli.v1"
        ),
        "context_contract_changed: true",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0283-r8-qdrant-real-closed-loop-smoke",
    ):
        assert required in report
