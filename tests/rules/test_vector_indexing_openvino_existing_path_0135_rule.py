from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "VECTOR_INDEXING_OPENVINO_EXISTING_PATH_0135.md"
CODE_RULE = ROOT / "doc" / "code-rules" / "0135_vector_indexing_openvino_existing_path_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0135_CHANGED_FILES.md"
TEST = ROOT / "tests" / "inference" / "test_vector_indexing_openvino_existing_path_0135.py"


def test_0135_documents_vector_jobs_use_existing_openvino_membrane() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0135 connects VectorIndexingJobPlan to the existing OpenVINO/E5 embedding membrane by tests only",
        "Do not create a new vector OpenVINO adapter",
        "VectorEmbeddingJob.item.text_for_embedding is already E5-prefixed",
        "OpenVINOEmbeddingText is the existing text contract",
        "build_embedding_vector is the existing vector validation contract",
        "Scheduler remains the orchestrator and does not import OpenVINO",
        "Qdrant projection remains a later adapter step",
        "SQLContextStore remains durable context authority",
        "code_rule_review: done",
        "code_rule_update_required: true",
    ]
    for phrase in required:
        assert phrase in text


def test_0135_code_rule_locks_no_parallel_vector_openvino_bridge() -> None:
    text = CODE_RULE.read_text(encoding="utf-8")
    required = [
        "Before adding a vector-indexing OpenVINO bridge",
        "reuse context.vector_indexing_job_plan.VectorEmbeddingJob",
        "reuse inference.openvino_embedding_adapter.OpenVINOEmbeddingText",
        "reuse inference.openvino_embedding_adapter.build_embedding_vector",
        "Do not create a parallel VectorOpenVINOEmbeddingAdapter",
        "Do not import OpenVINO from Scheduler, Dispatcher, PolicyEngine, RouteProxy, or context contracts",
    ]
    for phrase in required:
        assert phrase in text


def test_0135_manifest_changes_tests_and_docs_only() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tests/inference/test_vector_indexing_openvino_existing_path_0135.py",
        "tests/rules/test_vector_indexing_openvino_existing_path_0135_rule.py",
        "doc/architecture/VECTOR_INDEXING_OPENVINO_EXISTING_PATH_0135.md",
        "doc/code-rules/0135_vector_indexing_openvino_existing_path_rule.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/inference/vector_openvino_embedding_adapter.py",
        "src/runtime/vector_openvino_worker.py",
        "src/kernel/scheduler.py",
        "src/runtime/scheduler.py",
        "src/policy/engine.py",
        "src/runtime/route_proxy_runtime_minimal.py",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0135_integration_test_uses_existing_modules_not_new_adapter_names() -> None:
    text = TEST.read_text(encoding="utf-8")
    required = [
        "from context.vector_indexing_job_plan import",
        "from inference.openvino_embedding_adapter import",
        "OpenVINOEmbeddingText",
        "build_embedding_vector",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "VectorOpenVINOEmbeddingAdapter",
        "E5VectorBridgeAdapter",
        "import openvino",
        "from openvino",
    ]
    for phrase in forbidden:
        assert phrase not in text
