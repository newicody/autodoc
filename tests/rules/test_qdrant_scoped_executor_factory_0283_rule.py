from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/inference/qdrant_scoped_executor_factory_0283.py"
ARCHITECTURE = ROOT / "doc/architecture/QDRANT_SCOPED_EXECUTOR_FACTORY_COMPOSITION_0283.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0283_R3_QDRANT_SCOPED_EXECUTOR_FACTORY_COMPOSITION.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0283_R3_QDRANT_SCOPED_EXECUTOR_FACTORY_COMPOSITION.md"
REPORT = ROOT / "PHASE0283_R3_QDRANT_SCOPED_EXECUTOR_FACTORY_COMPOSITION_REPORT.md"


def test_factory_reuses_existing_builder_and_scope_wrapper():
    source = MODULE.read_text(encoding="utf-8")
    for required in (
        "build_qdrant_client_projection_executor",
        "inspect_qdrant_client_dependency",
        "SqlAuthorityScopedQdrantExecutor",
        "QdrantRealBindingConfigurationResult",
    ):
        assert required in source
    assert source.count("@dataclass(frozen=True, slots=True)") == 3


def test_factory_adds_no_parallel_architecture():
    source = MODULE.read_text(encoding="utf-8")
    for forbidden in (
        "class QdrantProjectionExecutor",
        "class QdrantClientProjectionExecutor",
        "LaboratoryManager",
        "Scheduler(",
        "ControlProxy(",
        "EventBus(",
        "memfd_create",
        "mmap(",
        "urlopen(",
        "requests.",
        "httpx.",
        "sqlite3",
        "psycopg",
    ):
        assert forbidden not in source
    for required in (
        '("new_qdrant_executor_added", False)',
        '("new_transport_added", False)',
        '("scheduler_path_added", False)',
        '("control_proxy_path_added", False)',
        '("event_bus_path_added", False)',
        '("shm_or_mmio_path_added", False)',
        '("data_operation_performed", False)',
        '("qdrant_write_performed", False)',
        '("qdrant_search_performed", False)',
    ):
        assert required in source


def test_factory_secret_boundary_is_explicit():
    source = MODULE.read_text(encoding="utf-8")
    assert "api_key_env_var" in source
    assert "os.environ" in source
    assert "secret_value_serialized" in source
    assert "top-secret" not in source


def test_phase_documents_architecture_stability():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT))
    for required in (
        "architecture_preserved: true",
        "existing_client_factory_reused: true",
        "existing_concrete_executor_reused: true",
        "existing_sql_scope_wrapper_reused: true",
        "new_qdrant_executor_added: false",
        "new_transport_added: false",
        "scheduler_modified: false",
        "control_proxy_integrated: false",
        "event_bus_integrated: false",
        "shm_or_mmio_integrated: false",
        "qdrant_write_performed: false",
        "qdrant_search_performed: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_versions_contract_and_names_r4():
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "live_path_uses_real_backend: true",
        "context_contract_version: missipy.qdrant.scoped_executor_factory_report.v1",
        "context_contract_changed: true",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0283-r4-qdrant-controlled-scheduler-projection-binding",
    ):
        assert required in report
