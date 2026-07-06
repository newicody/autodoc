from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_scheduler_vector_indexing_smoke.py"
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_VECTOR_INDEXING_RESULT_FRAME_0144.md"
RULE = ROOT / "doc" / "code-rules" / "0144_scheduler_vector_indexing_result_frame_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0144_CHANGED_FILES.md"


def test_0144_docs_lock_result_frame_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0144 writes a vector_indexing_result frame through the existing Scheduler route handler",
        "reuses tools/run_scheduler_vector_indexing_smoke.py",
        "reuses src/runtime/scheduler_route_handler_minimal.py",
        "reuses src/runtime/route_proxy_runtime_minimal.py",
        "does not create a result daemon or worker",
        "OpenVINO and Qdrant stay behind existing operator tools and adapters",
        "Do not modify Scheduler.run() in 0144",
        "code_rule_review: done",
        "code_rule_update_required: true",
    ]
    for phrase in required:
        assert phrase in text


def test_0144_code_rule_addendum_exists() -> None:
    text = RULE.read_text(encoding="utf-8")
    required = [
        "Vector indexing result frames must reuse the existing scheduler route handler",
        "Result frame IO must reuse src/runtime/route_proxy_runtime_minimal.py",
        "do not create a VectorIndexingResultWorker",
        "do not create LocalVectorIndexingOrchestrator",
        "do not import OpenVINO or Qdrant client into Scheduler or RouteProxy",
        "do not modify Scheduler.run()",
    ]
    for phrase in required:
        assert phrase in text


def test_0144_tool_does_not_import_openvino_qdrant_client_or_kernel_scheduler() -> None:
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = {"openvino", "qdrant_client", "scheduler", "policy", "src"}
    assert sorted(imports & forbidden) == []


def test_0144_tool_contains_result_frame_and_no_forbidden_parallel_runtime() -> None:
    text = TOOL.read_text(encoding="utf-8")
    required = [
        "vector_indexing_result",
        "write_scheduler_vector_indexing_result_frame",
        "extract_vector_indexing_smoke_result",
        "DEFAULT_RESULT_ROUTE_REF",
        "machine_vector_handoff",
        "result_frame_path",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "VectorIndexingResultWorker(",
        "LocalVectorIndexingOrchestrator(",
        "SchedulerOpenVINORunner(",
        "VectorOpenVINOEmbeddingAdapter(",
        "VectorQdrantProjectionAdapter(",
        "Scheduler.run(",
        "qdrant_client",
        "openvino.runtime",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0144_manifest_lists_changed_files_without_runtime_duplication() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tools/run_scheduler_vector_indexing_smoke.py",
        "tests/tools/test_scheduler_vector_indexing_result_frame_0144.py",
        "tests/rules/test_scheduler_vector_indexing_result_frame_0144_rule.py",
        "doc/architecture/SCHEDULER_VECTOR_INDEXING_RESULT_FRAME_0144.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/runtime/vector_indexing_result_worker.py",
        "src/inference/openvino_embedding_adapter.py",
        "src/inference/qdrant_projection_adapter.py",
        "src/runtime/route_proxy_runtime_minimal.py",
    ]
    for phrase in forbidden:
        assert phrase not in text
