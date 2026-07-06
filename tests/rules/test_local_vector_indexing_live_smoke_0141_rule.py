from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_local_vector_indexing_live_smoke.py"
DOC = ROOT / "doc" / "architecture" / "LOCAL_VECTOR_INDEXING_LIVE_SMOKE_0141.md"
RULE = ROOT / "doc" / "code-rules" / "0141_local_vector_indexing_live_smoke_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0141_CHANGED_FILES.md"


def test_0141_docs_lock_existing_surface_chain_and_no_new_wheels() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0141 composes the already validated existing operator surfaces",
        "tools/run_openvino_e5_live_smoke.py remains the OpenVINO/E5 execution surface",
        "tools/run_qdrant_projection_live_smoke.py remains the Qdrant projection execution surface",
        "Do not create LocalVectorIndexingOrchestrator",
        "Do not create VectorOpenVINOEmbeddingAdapter",
        "Do not create VectorQdrantProjectionAdapter",
        "strict full-vector handoff requires machine-readable E5 vector output",
        "Scheduler remains outside OpenVINO and Qdrant",
        "RouteProxy remains outside OpenVINO and Qdrant",
        "SQLContextStore remains durable authority",
        "code_rule_review: done",
        "code_rule_update_required: true",
    ]
    for phrase in required:
        assert phrase in text


def test_0141_code_rule_addendum_exists() -> None:
    text = RULE.read_text(encoding="utf-8")
    required = [
        "Before adding any local vector indexing runner",
        "reuse tools/run_openvino_e5_live_smoke.py",
        "reuse tools/run_qdrant_projection_live_smoke.py",
        "do not create LocalVectorIndexingOrchestrator",
        "do not parse human-only embedding previews as full vectors",
        "machine-readable vector handoff must be explicit",
    ]
    for phrase in required:
        assert phrase in text


def test_0141_tool_does_not_import_openvino_qdrant_or_scheduler_runtime() -> None:
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
        "scheduler",
        "runtime",
        "policy",
        "src",
        "inference",
        "context",
    }
    assert sorted(imports & forbidden) == []


def test_0141_manifest_lists_only_operator_docs_tests() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tools/run_local_vector_indexing_live_smoke.py",
        "tests/tools/test_local_vector_indexing_live_smoke_0141.py",
        "tests/rules/test_local_vector_indexing_live_smoke_0141_rule.py",
        "doc/architecture/LOCAL_VECTOR_INDEXING_LIVE_SMOKE_0141.md",
        "doc/code-rules/0141_local_vector_indexing_live_smoke_rule.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "src/inference/openvino_embedding_adapter.py",
        "src/inference/qdrant_projection_adapter.py",
        "LocalVectorIndexingOrchestrator.py",
        "VectorOpenVINOEmbeddingAdapter.py",
        "VectorQdrantProjectionAdapter.py",
    ]
    for phrase in forbidden:
        assert phrase not in text
