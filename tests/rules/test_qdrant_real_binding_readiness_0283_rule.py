from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/inference/"
    "qdrant_real_binding_readiness_0283.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "QDRANT_REAL_BINDING_READINESS_0283.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0283_R6_QDRANT_REAL_BINDING_READINESS.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0283_R6_QDRANT_REAL_BINDING_READINESS.md"
)
REPORT = (
    ROOT
    / "PHASE0283_R6_QDRANT_REAL_BINDING_READINESS_REPORT.md"
)


def test_readiness_reuses_r2_r3_and_dependency_inspection() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for required in (
        "QdrantRealBindingConfigurationResult",
        "inspect_qdrant_scoped_executor_factory",
        "inspect_qdrant_client_dependency",
        "get_collection",
    ):
        assert required in source

    assert source.count("@dataclass(frozen=True, slots=True)") == 3


def test_readiness_has_no_mutation_or_parallel_runtime() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for forbidden in (
        ".create_collection(",
        ".recreate_collection(",
        ".update_collection(",
        ".delete_collection(",
        ".upsert(",
        ".query_points(",
        "class Scheduler",
        "Scheduler(",
        "ControlProxy(",
        "EventBus(",
        "SharedMemory(",
        "memfd_create(",
        "mmap(",
        "sqlite3",
        "psycopg",
    ):
        assert forbidden not in source

    for required in (
        '("collection_created", False)',
        '("collection_updated", False)',
        '("collection_deleted", False)',
        '("qdrant_write_performed", False)',
        '("qdrant_search_performed", False)',
        '("sql_read_performed", False)',
        '("sql_write_performed", False)',
        '("qdrant_started", False)',
        '("new_scheduler_added", False)',
        '("scheduler_run_modified", False)',
        '("new_qdrant_executor_added", False)',
        '("new_transport_added", False)',
    ):
        assert required in source


def test_live_probe_is_explicit_and_read_only() -> None:
    source = MODULE.read_text(encoding="utf-8")

    assert "if not command.live_probe:" in source
    assert "live collection probe not requested" in source
    assert "client.get_collection(" in source
    assert "client.close()" in source
    assert "collection readiness probe failed" in source


def test_phase_documents_architecture_and_scope() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "architecture_preserved: true",
        "existing_r2_configuration_reused: true",
        "existing_r3_factory_inspection_reused: true",
        "existing_dependency_inspection_reused: true",
        "live_probe_is_explicit: true",
        "live_probe_read_only: true",
        "collection_created: false",
        "collection_updated: false",
        "collection_deleted: false",
        "qdrant_write_performed: false",
        "qdrant_search_performed: false",
        "sql_read_performed: false",
        "sql_write_performed: false",
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


def test_report_versions_contract_and_names_r7() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "live_path_uses_real_backend: true",
        (
            "context_contract_version: "
            "missipy.qdrant.real_binding_readiness.v1"
        ),
        "context_contract_changed: true",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0283-r7-qdrant-real-binding-preview-first-cli",
    ):
        assert required in report
