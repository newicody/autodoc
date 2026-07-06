from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_query_recall_rehydrate_contract_smoke.py"
DOC = ROOT / "doc" / "architecture" / "QUERY_RECALL_REHYDRATE_CONTRACT_0160.md"
RULE = ROOT / "doc" / "code-rules" / "0160_query_recall_rehydrate_contract_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0160_CHANGED_FILES.md"


def test_0160_files_exist() -> None:
    assert TOOL.exists()
    assert DOC.exists()
    assert RULE.exists()
    assert MANIFEST.exists()


def test_0160_tool_locks_existing_surface_reuse() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for token in [
        "tools/embed_e5.py",
        "tools/run_qdrant_recall_sql_rehydrate_smoke.py",
        "tools/run_qdrant_projection_live_smoke.py",
        "tools/search_e5_corpus.py",
        "src/inference/e5_pipeline.py",
        "src/inference/qdrant_projection_adapter.py",
        "src/context/sql_context_store.py",
        "DbApiSqlContextStore.get_record",
        "unique_sql_context_refs_from_recall",
        "query:",
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


def test_0160_docs_define_query_recall_rehydrate_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for token in ["query text", "query:", "Qdrant recall", "sql_ref", "0159", "SQL remains durable authority", "Qdrant remains projection/recall metadata"]:
        assert token in doc
    for token in ["Do not create", "VectorOpenVINOEmbeddingAdapter", "VectorQdrantProjectionAdapter", "QueryRecallOrchestrator"]:
        assert token in rule


def test_0160_manifest_changed_files_are_limited() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    for path in [
        "tools/run_query_recall_rehydrate_contract_smoke.py",
        "tests/tools/test_query_recall_rehydrate_contract_0160.py",
        "tests/rules/test_query_recall_rehydrate_contract_0160_rule.py",
        "doc/architecture/QUERY_RECALL_REHYDRATE_CONTRACT_0160.md",
        "doc/code-rules/0160_query_recall_rehydrate_contract_rule.md",
        "doc/docs/architecture/runtime/160_query_recall_rehydrate_contract.dot",
        "doc/CHANGELOG_0160_QUERY_RECALL_REHYDRATE_CONTRACT.md",
        "doc/manifests/MANIFEST_0160_CHANGED_FILES.md",
        "PHASE0160_TEST_REPORT.md",
    ]:
        assert path in text
    assert "src/inference/e5_pipeline.py" not in text
    assert "src/inference/qdrant_projection_adapter.py" not in text
    assert "src/context/sql_context_store.py" not in text
