from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_qdrant_recall_sql_rehydrate_smoke.py"
DOC = ROOT / "doc" / "architecture" / "QDRANT_RECALL_SQL_REHYDRATE_0159.md"
RULE = ROOT / "doc" / "code-rules" / "0159_qdrant_recall_sql_rehydrate_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0159_CHANGED_FILES.md"
def test_0159_files_exist() -> None:
    assert TOOL.exists(); assert DOC.exists(); assert RULE.exists(); assert MANIFEST.exists()
def test_0159_tool_locks_reuse_boundary() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for token in ["src/inference/qdrant_projection_adapter.py", "src/context/sql_context_store.py", "src/context/sql_context_hydrator.py", "DbApiSqlContextStore.get_record", "unique_sql_context_refs_from_recall", "SQL remains durable authority", "Qdrant remains projection/recall metadata", "SQLPersistenceWorker", "SQLOrchestrator", "LocalArtifactOrchestrator", "LocalVectorIndexingOrchestrator", "SchedulerOpenVINORunner", "VectorOpenVINOEmbeddingAdapter", "VectorQdrantProjectionAdapter", "QdrantRecallOrchestrator"]:
        assert token in text
    for forbidden_class in ["class SQLPersistenceWorker", "class SQLOrchestrator", "class LocalArtifactOrchestrator", "class LocalVectorIndexingOrchestrator", "class SchedulerOpenVINORunner", "class VectorOpenVINOEmbeddingAdapter", "class VectorQdrantProjectionAdapter", "class QdrantRecallOrchestrator"]:
        assert forbidden_class not in text
def test_0159_docs_define_recall_then_sql_rehydrate() -> None:
    doc = DOC.read_text(encoding="utf-8"); rule = RULE.read_text(encoding="utf-8")
    for token in ["Qdrant recall", "sql_ref", "DbApiSqlContextStore.get_record", "SQL remains durable authority", "Qdrant remains projection/recall metadata"]:
        assert token in doc
    for token in ["Do not create", "VectorQdrantProjectionAdapter", "SQLPersistenceWorker", "QdrantRecallOrchestrator"]:
        assert token in rule
def test_0159_manifest_changed_files_are_limited() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    for path in ["tools/run_qdrant_recall_sql_rehydrate_smoke.py", "tests/tools/test_qdrant_recall_sql_rehydrate_0159.py", "tests/rules/test_qdrant_recall_sql_rehydrate_0159_rule.py", "doc/architecture/QDRANT_RECALL_SQL_REHYDRATE_0159.md", "doc/code-rules/0159_qdrant_recall_sql_rehydrate_rule.md", "doc/docs/architecture/runtime/159_qdrant_recall_sql_rehydrate.dot", "doc/CHANGELOG_0159_QDRANT_RECALL_SQL_REHYDRATE.md", "doc/manifests/MANIFEST_0159_CHANGED_FILES.md", "PHASE0159_TEST_REPORT.md"]:
        assert path in text
    assert "src/inference/qdrant_projection_adapter.py" not in text
    assert "src/context/sql_context_store.py" not in text
