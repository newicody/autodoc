from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_qdrant_live_recall_sql_rehydrate_smoke.py"
DOC = ROOT / "doc" / "architecture" / "QDRANT_LIVE_RECALL_SQL_REHYDRATE_0161.md"
RULE = ROOT / "doc" / "code-rules" / "0161_qdrant_live_recall_sql_rehydrate_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0161_CHANGED_FILES.md"


def test_0161_files_exist() -> None:
    assert TOOL.exists()
    assert DOC.exists()
    assert RULE.exists()
    assert MANIFEST.exists()


def test_0161_tool_locks_existing_live_recall_surfaces() -> None:
    text = TOOL.read_text(encoding="utf-8")

    for token in [
        "tools/embed_e5.py",
        "tools/run_qdrant_projection_live_smoke.py",
        "tools/run_qdrant_recall_sql_rehydrate_smoke.py",
        "src/inference/qdrant_projection_adapter.py",
        "src/context/sql_context_store.py",
        "QdrantProjectionExecutor.search_vector",
        "QdrantProjectionAdapter.recall_by_vector",
        "QdrantRecallQuery",
        "QdrantRecallResult",
        "unique_sql_context_refs_from_recall",
        "/collections/{collection}/points/search",
        "/points/search",
        "DbApiSqlContextStore.get_record",
        "SQL remains durable authority",
        "Qdrant remains projection/recall metadata",
        "SQLPersistenceWorker",
        "SQLOrchestrator",
        "LocalArtifactOrchestrator",
        "LocalVectorIndexingOrchestrator",
        "SchedulerOpenVINORunner",
        "VectorOpenVINOEmbeddingAdapter",
        "VectorQdrantProjectionAdapter",
        "QdrantRecallOrchestrator",
        "QueryRecallOrchestrator",
    ]:
        assert token in text

    for forbidden_class in [
        "class SQLPersistenceWorker",
        "class SQLOrchestrator",
        "class LocalArtifactOrchestrator",
        "class LocalVectorIndexingOrchestrator",
        "class SchedulerOpenVINORunner",
        "class VectorOpenVINOEmbeddingAdapter",
        "class VectorQdrantProjectionAdapter",
        "class QdrantRecallOrchestrator",
        "class QueryRecallOrchestrator",
    ]:
        assert forbidden_class not in text


def test_0161_docs_define_live_recall_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")

    for token in [
        "live Qdrant recall",
        "query embedding",
        "/points/search",
        "sql_ref",
        "0159",
        "SQL remains durable authority",
        "Qdrant remains projection/recall metadata",
    ]:
        assert token in doc

    for token in [
        "Do not create",
        "VectorOpenVINOEmbeddingAdapter",
        "VectorQdrantProjectionAdapter",
        "QdrantRecallOrchestrator",
    ]:
        assert token in rule


def test_0161_manifest_changed_files_are_limited() -> None:
    text = MANIFEST.read_text(encoding="utf-8")

    for path in [
        "tools/run_qdrant_live_recall_sql_rehydrate_smoke.py",
        "tests/tools/test_qdrant_live_recall_sql_rehydrate_0161.py",
        "tests/rules/test_qdrant_live_recall_sql_rehydrate_0161_rule.py",
        "doc/architecture/QDRANT_LIVE_RECALL_SQL_REHYDRATE_0161.md",
        "doc/code-rules/0161_qdrant_live_recall_sql_rehydrate_rule.md",
        "doc/docs/architecture/runtime/161_qdrant_live_recall_sql_rehydrate.dot",
        "doc/CHANGELOG_0161_QDRANT_LIVE_RECALL_SQL_REHYDRATE.md",
        "doc/manifests/MANIFEST_0161_CHANGED_FILES.md",
        "PHASE0161_TEST_REPORT.md",
    ]:
        assert path in text

    assert "src/inference/qdrant_projection_adapter.py" not in text
    assert "src/context/sql_context_store.py" not in text
