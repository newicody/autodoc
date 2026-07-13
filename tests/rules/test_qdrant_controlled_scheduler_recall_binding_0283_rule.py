from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/context/"
    "scheduler_managed_qdrant_recall_binding_0283.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "QDRANT_CONTROLLED_SCHEDULER_RECALL_BINDING_0283.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0283_R5_QDRANT_CONTROLLED_SCHEDULER_RECALL_BINDING.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0283_R5_QDRANT_CONTROLLED_SCHEDULER_RECALL_BINDING.md"
)
REPORT = (
    ROOT
    / "PHASE0283_R5_QDRANT_CONTROLLED_SCHEDULER_RECALL_BINDING_REPORT.md"
)


def test_binding_reuses_0263_r3_and_sql_store() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for required in (
        "run_scheduler_managed_qdrant_recall_sql_rehydrate_usage",
        "SchedulerManagedQdrantRecallSqlRehydrateRequest",
        "default_query_ref_from_embedding_report",
        "build_qdrant_scoped_executor_binding",
        "QdrantScopedExecutorFactoryError",
    ):
        assert required in source

    assert source.count("@dataclass(frozen=True, slots=True)") == 3


def test_binding_does_not_add_parallel_architecture() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for forbidden in (
        "class Scheduler",
        "Scheduler(",
        "ControlProxy(",
        "EventBus(",
        "SharedMemory(",
        "memfd_create(",
        "mmap(",
        "urlopen(",
        "requests.",
        "httpx.",
        "sqlite3",
        "psycopg",
    ):
        assert forbidden not in source

    for required in (
        '("new_scheduler_added", False)',
        '("scheduler_run_modified", False)',
        '("new_qdrant_executor_added", False)',
        '("new_transport_added", False)',
        '("control_proxy_integrated", False)',
        '("event_bus_integrated", False)',
        '("shm_or_mmio_integrated", False)',
        '("qdrant_write_performed", False)',
        '("sql_write_performed", False)',
    ):
        assert required in source


def test_preview_and_authority_boundaries_are_explicit() -> None:
    source = MODULE.read_text(encoding="utf-8")

    assert "if not command.execute:" in source
    assert "binding_builder(" in source
    assert "binding.close()" in source
    assert "qdrant_returns_refs_only" in source
    assert "sql_remains_authority" in source
    assert "preview_reads_sql" in source
    assert "recall limit exceeds configured max_recall_hits" in source


def test_phase_documents_architecture_and_scope() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "architecture_preserved: true",
        "existing_0263_usage_reused: true",
        "existing_r3_factory_reused: true",
        "existing_sql_store_reused: true",
        "preview_constructs_client: false",
        "preview_reads_sql: false",
        "qdrant_search_requires_execute: true",
        "qdrant_returns_refs_only: true",
        "sql_remains_authority: true",
        "new_scheduler_added: false",
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


def test_report_versions_contract_and_names_r6() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "live_path_uses_real_backend: true",
        (
            "context_contract_version: "
            "missipy.qdrant.controlled_scheduler_recall_binding.v1"
        ),
        "context_contract_changed: true",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0283-r6-qdrant-real-binding-readiness",
    ):
        assert required in report
