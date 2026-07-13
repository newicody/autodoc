from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "QDRANT_REAL_BINDING_REUSE_AUDIT_0283.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0283_R1_QDRANT_REAL_BINDING_REUSE_AUDIT.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0283_R1_QDRANT_REAL_BINDING_REUSE_AUDIT.md"
)
REPORT = (
    ROOT
    / "PHASE0283_R1_QDRANT_REAL_BINDING_REUSE_AUDIT_REPORT.md"
)

SURFACES = {
    "src/context/controlled_real_qdrant_executor_reuse_audit_0271.py": (
        "live_executor_found",
        "existing_protocol_must_be_reused",
        "sql_remains_authority",
        "qdrant_remains_projection_recall_only",
    ),
    "src/inference/qdrant_projection_adapter.py": (
        "QdrantProjectionExecutor",
        "upsert_points",
        "search_vector",
        "build_qdrant_projection_batch",
        "unique_sql_context_refs_from_recall",
    ),
    "src/inference/qdrant_client_projection_executor.py": (
        'qdrant-client',
        '1.18.0',
        "QdrantClientEffectGate",
        "QdrantClientProjectionExecutor",
        "build_qdrant_client_projection_executor",
        "inspect_qdrant_client_dependency",
    ),
    "src/inference/qdrant_sql_authority_scope.py": (
        "QdrantSqlAuthorityScope",
        "QdrantStrictGrpcTransportPolicy",
        "SqlAuthorityScopedQdrantExecutor",
        "derive_sqlite_authority_scope",
        "sql_authority_ref",
    ),
    "src/context/scheduler_managed_embedding_qdrant_projection_usage_0262.py": (
        "SchedulerManagedEmbeddingQdrantProjectionRequest",
        "run_scheduler_managed_embedding_qdrant_projection_usage",
        "execute requires an injected QdrantProjectionExecutor",
    ),
    "src/context/scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263.py": (
        "SchedulerManagedQdrantRecallSqlRehydrateRequest",
        "run_scheduler_managed_qdrant_recall_sql_rehydrate_usage",
        "unique_sql_context_refs_from_recall",
    ),
    "tools/check_qdrant_client_projection_executor_0271.py": (),
    "tools/check_qdrant_sql_authority_scope_0271.py": (),
}


def test_audit_reuses_all_existing_qdrant_surfaces() -> None:
    audit = ARCHITECTURE.read_text(encoding="utf-8")

    for relative, markers in SURFACES.items():
        path = ROOT / relative
        assert path.is_file(), relative
        source = path.read_text(encoding="utf-8")
        assert relative.split("/")[-1] in audit
        for marker in markers:
            assert marker in source


def test_audit_conclusion_rejects_duplicate_executor_and_authority() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "previous_reuse_audit_reused: true",
        "existing_real_executor_found: true",
        "existing_sql_authority_scope_found: true",
        "new_executor_module_justified: false",
        "existing_executor_must_be_reused: true",
        "sql_authority_scope_must_wrap_executor: true",
        "scheduler_managed_projection_usage_reused: true",
        "scheduler_managed_recall_usage_reused: true",
        "binding_surface_missing: true",
        "new_qdrant_authority_added: false",
    ):
        assert required in combined


def test_audit_is_add_only_and_effect_free() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )

    for required in (
        "runtime_source_modified: false",
        "new_runtime_module_added: false",
        "new_executor_added: false",
        "new_scheduler_added: false",
        "new_worker_added: false",
        "qdrant_collection_creation_added: false",
        "qdrant_write_performed: false",
        "qdrant_search_performed: false",
        "network_used: false",
        "sql_write_performed: false",
        "scheduler_modified: false",
        "external_dependencies_added: false",
        "projects_repository_change_required: false",
    ):
        assert required in combined


def test_binding_order_and_next_patch_are_explicit() -> None:
    audit = ARCHITECTURE.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")

    for required in (
        "QdrantClientEffectGate",
        "build_qdrant_client_projection_executor",
        "SqlAuthorityScopedQdrantExecutor",
        "inject into 0262 projection or 0263 recall",
        "0283-r2  immutable binding configuration and policy",
    ):
        assert required in audit

    assert (
        "next_patch: "
        "0283-r2-qdrant-real-binding-configuration-contract"
        in report
    )


def test_phase_report_contains_complete_code_rule_review() -> None:
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
