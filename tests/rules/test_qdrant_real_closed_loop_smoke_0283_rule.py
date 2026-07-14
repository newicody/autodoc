from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = (
    ROOT
    / "tools/run_qdrant_real_closed_loop_smoke_0283.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "QDRANT_REAL_CLOSED_LOOP_SMOKE_0283.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0283_R8_QDRANT_REAL_CLOSED_LOOP_SMOKE.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0283_R8_QDRANT_REAL_CLOSED_LOOP_SMOKE.md"
)
REPORT = (
    ROOT
    / "PHASE0283_R8_QDRANT_REAL_CLOSED_LOOP_SMOKE_REPORT.md"
)


def test_smoke_reuses_existing_0261_r4_r5_r6() -> None:
    source = TOOL.read_text(encoding="utf-8")

    for required in (
        "run_scheduler_managed_sql_ref_openvino_embedding_usage",
        "run_qdrant_controlled_scheduler_projection_binding",
        "run_qdrant_controlled_scheduler_recall_binding",
        "inspect_qdrant_real_binding_readiness",
        "derive_sqlite_authority_scope",
    ):
        assert required in source


def test_smoke_has_preview_and_persistent_point_gates() -> None:
    source = TOOL.read_text(encoding="utf-8")

    for required in (
        '"--execute"',
        '"--authorize-smoke"',
        '"--authorize-persistent-smoke-point"',
        "--execute requires --authorize-smoke",
        "--authorize-persistent-smoke-point",
        "--execute requires --policy-decision-id",
        "automatic_cleanup_performed",
    ):
        assert required in source


def test_smoke_does_not_administer_qdrant_or_parallel_runtime() -> None:
    source = TOOL.read_text(encoding="utf-8")

    for forbidden in (
        ".create_collection(",
        ".recreate_collection(",
        ".update_collection(",
        ".delete_collection(",
        ".delete_points(",
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
        '"scheduler_modified": False',
        '"new_scheduler_added": False',
        '"new_qdrant_executor_added": False',
        '"new_transport_added": False',
        '"control_proxy_integrated": False',
        '"event_bus_integrated": False',
        '"shm_or_mmio_integrated": False',
    ):
        assert required in source


def test_execute_requires_real_384_dimension_e5() -> None:
    source = TOOL.read_text(encoding="utf-8")

    assert "args.vector_dimension != 384" in source
    assert "multilingual-e5-small" in source
    assert "execute embedding must not use demo model" in source
    assert '"real_openvino_e5_executed": True' in source


def test_phase_documents_closed_loop_and_cleanup() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "architecture_preserved: true",
        "preview_first: true",
        "existing_0261_embedding_usage_reused: true",
        "existing_r4_projection_binding_reused: true",
        "existing_r5_recall_binding_reused: true",
        "existing_r6_readiness_reused: true",
        "real_sql_authority_used_on_execute: true",
        "real_openvino_e5_used_on_execute: true",
        "real_qdrant_projection_used_on_execute: true",
        "real_qdrant_recall_used_on_execute: true",
        "qdrant_returns_references_only: true",
        "sql_rehydration_verified: true",
        "automatic_cleanup_performed: false",
        "collection_created: false",
        "collection_updated: false",
        "collection_deleted: false",
        "scheduler_modified: false",
        "new_qdrant_executor_added: false",
        "new_transport_added: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_closes_0283_and_names_0284() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: ready_for_operator_smoke",
        "live_path_uses_real_backend: true",
        (
            "context_contract_version: "
            "missipy.qdrant.real_closed_loop_smoke.v1"
        ),
        "context_contract_changed: true",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "phase_0283_closed: true",
        "0284-specialists-laboratories-chain",
    ):
        assert required in report
