from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "VECTOR_INDEXING_QDRANT_EXISTING_PATH_0136.md"
CODE_RULE = ROOT / "doc" / "code-rules" / "0136_vector_indexing_qdrant_existing_path_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0136_CHANGED_FILES.md"
TEST = ROOT / "tests" / "inference" / "test_vector_indexing_qdrant_existing_path_0136.py"


def test_0136_documents_vector_jobs_use_existing_qdrant_projection_path() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0136 connects VectorProjectionJob to the existing Qdrant projection adapter by tests and integration documentation",
        "Do not create a parallel VectorQdrantProjectionAdapter",
        "src/inference/qdrant_projection_adapter.py is the existing Qdrant projection membrane",
        "context.vector_collection_registry.VectorCollectionRegistry remains the collection registry",
        "context.vector_indexing_job_plan.VectorProjectionJob remains the projection job contract",
        "Scheduler remains the orchestrator and does not import Qdrant",
        "RouteProxy remains outside Qdrant projection",
        "SQLContextStore remains durable context authority",
        "Qdrant stores projections and recall indexes, not durable truth",
        "code_rule_review: done",
        "code_rule_update_required: true",
    ]
    for phrase in required:
        assert phrase in text


def test_0136_code_rule_locks_no_parallel_vector_qdrant_bridge() -> None:
    text = CODE_RULE.read_text(encoding="utf-8")
    required = [
        "Before adding a vector-indexing Qdrant bridge",
        "reuse or extend src/inference/qdrant_projection_adapter.py",
        "reuse context.vector_collection_registry.VectorCollectionRegistry",
        "reuse context.vector_indexing_job_plan.VectorProjectionJob",
        "Do not create a parallel VectorQdrantProjectionAdapter",
        "Do not import Qdrant from Scheduler, Dispatcher, PolicyEngine, RouteProxy, or context contracts",
    ]
    for phrase in required:
        assert phrase in text


def test_0136_manifest_changes_tests_and_docs_only() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tests/inference/test_vector_indexing_qdrant_existing_path_0136.py",
        "tests/rules/test_vector_indexing_qdrant_existing_path_0136_rule.py",
        "doc/architecture/VECTOR_INDEXING_QDRANT_EXISTING_PATH_0136.md",
        "doc/code-rules/0136_vector_indexing_qdrant_existing_path_rule.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/inference/vector_qdrant_projection_adapter.py",
        "src/runtime/vector_qdrant_worker.py",
        "src/kernel/scheduler.py",
        "src/runtime/scheduler.py",
        "src/policy/engine.py",
        "src/runtime/route_proxy_runtime_minimal.py",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0136_integration_test_uses_existing_paths_not_new_adapter_names() -> None:
    text = TEST.read_text(encoding="utf-8")
    required = [
        "qdrant_projection_adapter.py",
        "vector_indexing_job_plan.py",
        "vector_collection_registry.py",
        "VectorProjectionJob",
        "VectorCollectionRegistry",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "VectorQdrantProjectionAdapter",
        "QdrantVectorBridgeAdapter",
        "from qdrant_client import QdrantClient",
    ]
    for phrase in forbidden:
        assert phrase not in text
