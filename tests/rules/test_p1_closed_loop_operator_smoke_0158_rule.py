from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_p1_closed_loop_operator_smoke.py"
DOC = ROOT / "doc" / "architecture" / "P1_CLOSED_LOOP_OPERATOR_COMPOSITION_0158.md"
RULE = ROOT / "doc" / "code-rules" / "0158_p1_closed_loop_operator_composition_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0158_CHANGED_FILES.md"


def test_0158_files_exist() -> None:
    assert TOOL.exists()
    assert DOC.exists()
    assert RULE.exists()
    assert MANIFEST.exists()


def test_0158_tool_reuses_existing_p1_surfaces() -> None:
    text = TOOL.read_text(encoding="utf-8")

    required = [
        "tools/run_local_artifact_vector_indexing_runner.py",
        "tools/run_sql_persistence_handoff_smoke.py",
        "tools/run_sql_context_store_persistence_smoke.py",
        "tools/run_sql_context_store_write_surface_audit.py",
        "tools/run_sql_context_store_controlled_write_smoke.py",
        "DbApiSqlContextStore.upsert_record",
        "SQLPersistenceWorker",
        "SQLOrchestrator",
        "LocalArtifactOrchestrator",
        "LocalVectorIndexingOrchestrator",
        "SchedulerOpenVINORunner",
        "VectorOpenVINOEmbeddingAdapter",
        "VectorQdrantProjectionAdapter",
    ]
    for token in required:
        assert token in text

    forbidden_class_defs = [
        "class SQLPersistenceWorker",
        "class SQLOrchestrator",
        "class LocalArtifactOrchestrator",
        "class LocalVectorIndexingOrchestrator",
        "class SchedulerOpenVINORunner",
        "class VectorOpenVINOEmbeddingAdapter",
        "class VectorQdrantProjectionAdapter",
    ]
    for token in forbidden_class_defs:
        assert token not in text


def test_0158_docs_lock_operator_only_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")

    for token in [
        "operator-only composition",
        "0145",
        "0148",
        "0149",
        "0150",
        "0151/0152",
        "readback_ok",
        "SQL remains durable authority",
    ]:
        assert token in doc

    for forbidden in [
        "SQLPersistenceWorker",
        "SQLOrchestrator",
        "LocalArtifactOrchestrator",
        "LocalVectorIndexingOrchestrator",
        "SchedulerOpenVINORunner",
        "VectorOpenVINOEmbeddingAdapter",
        "VectorQdrantProjectionAdapter",
    ]:
        assert forbidden in rule


def test_0158_manifest_changed_files_are_limited() -> None:
    text = MANIFEST.read_text(encoding="utf-8")

    allowed = [
        "tools/run_p1_closed_loop_operator_smoke.py",
        "tests/tools/test_p1_closed_loop_operator_smoke_0158.py",
        "tests/rules/test_p1_closed_loop_operator_smoke_0158_rule.py",
        "doc/architecture/P1_CLOSED_LOOP_OPERATOR_COMPOSITION_0158.md",
        "doc/code-rules/0158_p1_closed_loop_operator_composition_rule.md",
        "doc/docs/architecture/runtime/158_p1_closed_loop_operator_composition.dot",
        "doc/CHANGELOG_0158_P1_CLOSED_LOOP_OPERATOR_COMPOSITION.md",
        "doc/manifests/MANIFEST_0158_CHANGED_FILES.md",
        "PHASE0158_TEST_REPORT.md",
    ]
    for path in allowed:
        assert path in text

    assert "src/runtime/" not in text
    assert "src/inference/" not in text
    assert "src/context/sql_context_store.py" not in text
