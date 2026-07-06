from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_local_vector_indexing_smoke.py"
DOC = ROOT / "doc" / "architecture" / "LOCAL_VECTOR_INDEXING_TEST_READINESS_0137.md"
CODE_RULE = ROOT / "doc" / "code-rules" / "0137_local_vector_indexing_test_readiness_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0137_CHANGED_FILES.md"


def test_0137_documents_steps_before_first_real_test() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0137 is a readiness gate, not a runtime implementation",
        "stabilize 0136-r1 before running the first local vector-indexing smoke test",
        "run OpenVINO/E5 through the existing inference membrane",
        "run Qdrant through the existing projection adapter",
        "then wire Scheduler to enqueue the existing VectorIndexingJobPlan",
        "Do not create VectorOpenVINOEmbeddingAdapter",
        "Do not create VectorQdrantProjectionAdapter",
        "Scheduler remains the orchestrator",
        "SQLContextStore remains durable authority",
        "code_rule_review: done",
        "code_rule_update_required: true",
    ]
    for phrase in required:
        assert phrase in text


def test_0137_code_rule_requires_readiness_inventory_before_runner() -> None:
    text = CODE_RULE.read_text(encoding="utf-8")
    required = [
        "Before adding a local vector-indexing runner",
        "run tools/plan_local_vector_indexing_smoke.py",
        "reuse existing RouteProxyRuntime, Scheduler route handler, OpenVINO/E5 membrane, Qdrant projection adapter, and SQLContextStore",
        "Do not create a new scheduler, runtime, OpenVINO adapter, Qdrant adapter, or orchestrator for the smoke test",
    ]
    for phrase in required:
        assert phrase in text


def test_0137_tool_has_no_runtime_or_backend_imports() -> None:
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = {
        "openvino",
        "qdrant",
        "qdrant_client",
        "psycopg",
        "sqlite3",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "src",
    }
    assert sorted(imports & forbidden) == []


def test_0137_manifest_only_adds_tool_docs_and_tests() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tools/plan_local_vector_indexing_smoke.py",
        "tests/tools/test_local_vector_indexing_smoke_readiness_0137.py",
        "tests/rules/test_local_vector_indexing_smoke_readiness_0137_rule.py",
        "doc/architecture/LOCAL_VECTOR_INDEXING_TEST_READINESS_0137.md",
        "doc/code-rules/0137_local_vector_indexing_test_readiness_rule.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/runtime/scheduler_route_handler_minimal.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "src/inference/openvino_embedding_adapter.py",
        "src/inference/qdrant_projection_adapter.py",
    ]
    for phrase in forbidden:
        assert phrase not in text
