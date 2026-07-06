from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_scheduler_vector_indexing_smoke.py"
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_VECTOR_INDEXING_SMOKE_0143.md"
RULE = ROOT / "doc" / "code-rules" / "0143_scheduler_vector_indexing_smoke_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0143_CHANGED_FILES.md"


def test_0143_docs_lock_scheduler_vector_smoke_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0143 writes a vector indexing request frame through the existing Scheduler route handler",
        "reuses src/runtime/scheduler_route_handler_minimal.py",
        "reuses src/runtime/route_proxy_runtime_minimal.py",
        "reuses tools/run_local_vector_indexing_live_smoke.py",
        "OpenVINO and Qdrant stay outside Scheduler and RouteProxy",
        "Do not create SchedulerOpenVINORunner",
        "Do not create LocalVectorIndexingOrchestrator",
        "Do not modify Scheduler.run() in 0143",
        "code_rule_review: done",
        "code_rule_update_required: true",
    ]
    for phrase in required:
        assert phrase in text


def test_0143_code_rule_addendum_exists() -> None:
    text = RULE.read_text(encoding="utf-8")
    required = [
        "Scheduler vector indexing smoke must reuse the existing scheduler route handler",
        "RouteProxy frame IO must reuse src/runtime/route_proxy_runtime_minimal.py",
        "Strict vector execution must reuse tools/run_local_vector_indexing_live_smoke.py",
        "do not create SchedulerOpenVINORunner",
        "do not create LocalVectorIndexingOrchestrator",
        "do not modify Scheduler.run()",
    ]
    for phrase in required:
        assert phrase in text


def test_0143_tool_does_not_import_openvino_qdrant_client_or_kernel_scheduler() -> None:
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = {"openvino", "qdrant_client", "scheduler", "policy", "src"}
    assert sorted(imports & forbidden) == []


def test_0143_tool_contains_required_existing_surface_strings_and_no_forbidden_workers() -> None:
    text = TOOL.read_text(encoding="utf-8")
    required = [
        "src/runtime/scheduler_route_handler_minimal.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "tools/run_local_vector_indexing_live_smoke.py",
        "vector_embedding_request",
        "--strict-vector-handoff",
        "scheduler_run_modified",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "SchedulerOpenVINORunner(",
        "LocalVectorIndexingOrchestrator(",
        "VectorOpenVINOEmbeddingAdapter(",
        "VectorQdrantProjectionAdapter(",
        "Scheduler.run(",
        "qdrant_client",
        "openvino.runtime",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0143_manifest_lists_operator_tool_only() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tools/run_scheduler_vector_indexing_smoke.py",
        "tests/tools/test_scheduler_vector_indexing_smoke_0143.py",
        "tests/rules/test_scheduler_vector_indexing_smoke_0143_rule.py",
        "doc/architecture/SCHEDULER_VECTOR_INDEXING_SMOKE_0143.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/inference/openvino_embedding_adapter.py",
        "src/inference/qdrant_projection_adapter.py",
        "src/runtime/route_proxy_runtime_minimal.py",
    ]
    for phrase in forbidden:
        assert phrase not in text
