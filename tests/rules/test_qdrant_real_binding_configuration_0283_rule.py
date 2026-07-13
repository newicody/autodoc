from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/inference/qdrant_real_binding_configuration_0283.py"
)
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "QDRANT_REAL_BINDING_CONFIGURATION_CONTRACT_0283.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0283_R2_QDRANT_REAL_BINDING_CONFIGURATION_CONTRACT.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0283_R2_QDRANT_REAL_BINDING_CONFIGURATION_CONTRACT.md"
)
REPORT = (
    ROOT
    / "PHASE0283_R2_QDRANT_REAL_BINDING_CONFIGURATION_CONTRACT_REPORT.md"
)


def test_contract_reuses_all_existing_configuration_types() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for required in (
        "QdrantClientConnectionConfig",
        "QdrantClientEffectGate",
        "QdrantSqlAuthorityScope",
        "QdrantStrictGrpcTransportPolicy",
        "QdrantProjectionTarget",
        "QdrantProjectionPolicy",
    ):
        assert required in source

    assert source.count("@dataclass(frozen=True, slots=True)") == 3


def test_contract_has_no_factory_secret_lookup_or_effect_path() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for forbidden in (
        "build_qdrant_client_projection_executor(",
        "inspect_qdrant_client_dependency(",
        "os.environ",
        "getenv(",
        "urlopen(",
        "requests.",
        "httpx.",
        "socket.",
        "upsert_points(",
        "search_vector(",
        "Scheduler(",
        "sqlite3",
        "psycopg",
    ):
        assert forbidden not in source

    for required in (
        '("dependency_inspection_performed", False)',
        '("client_constructed", False)',
        '("external_call_performed", False)',
        '("qdrant_write_performed", False)',
        '("qdrant_search_performed", False)',
        '("sql_write_performed", False)',
        '("scheduler_modified", False)',
    ):
        assert required in source


def test_contract_locks_shared_collection_sql_authority_and_secret_boundary() -> None:
    source = MODULE.read_text(encoding="utf-8")

    for required in (
        "allowed_collection_names",
        "autodoc_context_embeddings",
        "require_sql_context_ref",
        "require_normalized_vectors",
        "api_key_env_var",
        "secret_value_serialized",
        "require_loopback",
        "require_strict_data_grpc",
        "require_exact_effect_gate",
    ):
        assert required in source


def test_phase_documents_new_module_justification_and_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "reuse_audit_completed: true",
        "existing_suitable_configuration_contract_found: false",
        "existing_executor_reused: true",
        "existing_sql_scope_reused: true",
        "new_runtime_module_added: true",
        "new_executor_added: false",
        "new_client_factory_added: false",
        "network_used: false",
        "qdrant_write_performed: false",
        "qdrant_search_performed: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined


def test_report_versions_contract_and_names_r3() -> None:
    report = REPORT.read_text(encoding="utf-8")

    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "live_path_uses_real_backend: n/a",
        (
            "context_contract_version: "
            "missipy.qdrant.real_binding_configuration.v1"
        ),
        "context_contract_changed: true",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "0283-r3-qdrant-scoped-executor-factory-composition",
    ):
        assert required in report
