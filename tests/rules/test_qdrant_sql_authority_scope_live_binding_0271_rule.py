from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTION = ROOT / "tools/run_scheduler_managed_embedding_qdrant_projection_0262.py"
RECALL = ROOT / "tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py"
CORE = ROOT / "src/context/production_prototype_smoke_composition_0269.py"
CLI = ROOT / "tools/run_production_prototype_smoke_composition_0269.py"
DOC = ROOT / "doc/architecture/QDRANT_SQL_AUTHORITY_SCOPE_LIVE_BINDING_0271.md"
RULE = ROOT / "doc/code-rules/0271_qdrant_sql_authority_scope_live_binding_rule.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0271_QDRANT_SQL_AUTHORITY_SCOPE_LIVE_BINDING_CHANGED_FILES.md"


def test_0271_r5_wraps_existing_live_executor_in_both_tools() -> None:
    projection = PROJECTION.read_text(encoding="utf-8")
    recall = RECALL.read_text(encoding="utf-8")
    for text in (projection, recall):
        assert "SqlAuthorityScopedQdrantExecutor" in text
        assert "derive_sqlite_authority_scope" in text
        assert "QdrantStrictGrpcTransportPolicy" in text
        assert 'payload["sql_authority_ref"]' in text
        assert 'payload["strict_data_grpc"]' in text
    assert 'parser.add_argument("--db-path"' in projection
    assert "allow_write=True" in projection
    assert "allow_search=True" in recall


def test_0271_r5_composition_passes_one_store_scope_and_requires_proofs() -> None:
    core = CORE.read_text(encoding="utf-8")
    cli = CLI.read_text(encoding="utf-8")
    assert 'execute_0262.extend(["--db-path", str(command.database_path), *live_args])' in core
    assert '"--sql-authority-namespace"' in core
    assert '"--strict-data-grpc"' in core
    assert '"qdrant_projection_scoped"' in core
    assert '"qdrant_recall_scoped"' in core
    assert '"sql_authority_ref"' in core
    assert 'parser.add_argument("--strict-data-grpc"' in cli
    assert 'parser.add_argument("--sql-authority-namespace"' in cli


def test_0271_r5_keeps_service_sql_and_shm_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PROJECTION, RECALL, CORE, CLI, DOC, RULE)
    )
    for forbidden in (
        "rc-service",
        "rc-update",
        "create_collection",
        "recreate_collection",
        "delete_collection",
        "RuntimeManager",
        "Scheduler.run(",
        "multiprocessing.shared_memory",
        "mmap.mmap",
    ):
        assert forbidden not in combined
    assert "SQL remains the durable authority" in RULE.read_text(encoding="utf-8")
    assert "legacy unscoped hits" in DOC.read_text(encoding="utf-8")


def test_0271_r5_manifest_lists_only_existing_bindings_and_phase_surfaces() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for path in (
        "tools/run_scheduler_managed_embedding_qdrant_projection_0262.py",
        "tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py",
        "src/context/production_prototype_smoke_composition_0269.py",
        "tools/run_production_prototype_smoke_composition_0269.py",
    ):
        assert path in manifest
    assert "RuntimeManager" not in manifest
