from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL_TOOL = ROOT / "tools" / "run_local_vector_indexing_live_smoke.py"
QDRANT_TOOL = ROOT / "tools" / "run_qdrant_projection_live_smoke.py"
DOC = ROOT / "doc" / "architecture" / "MACHINE_VECTOR_HANDOFF_0142.md"
RULE = ROOT / "doc" / "code-rules" / "0142_machine_vector_handoff_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0142_CHANGED_FILES.md"


def test_0142_docs_lock_strict_machine_vector_handoff() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0142 reuses tools/embed_e5.py --format json --full-vector",
        "0142 reuses tools/run_qdrant_projection_live_smoke.py --vector-json",
        "Do not parse values_preview as a full vector",
        "Do not create VectorOpenVINOEmbeddingAdapter",
        "Do not create VectorQdrantProjectionAdapter",
        "Scheduler remains outside OpenVINO and Qdrant",
        "RouteProxy remains outside OpenVINO and Qdrant",
        "SQLContextStore remains durable authority",
        "code_rule_review: done",
        "code_rule_update_required: true",
    ]
    for phrase in required:
        assert phrase in text


def test_0142_code_rule_addendum_exists() -> None:
    text = RULE.read_text(encoding="utf-8")
    required = [
        "machine-readable vector handoff must use tools/embed_e5.py --format json --full-vector",
        "Qdrant smoke may consume that file through --vector-json",
        "never parse values_preview as a full vector",
        "do not create LocalVectorIndexingOrchestrator",
        "do not create VectorOpenVINOEmbeddingAdapter",
        "do not create VectorQdrantProjectionAdapter",
    ]
    for phrase in required:
        assert phrase in text


def test_0142_operator_tools_do_not_import_openvino_qdrant_client_or_scheduler() -> None:
    forbidden = {"openvino", "qdrant_client", "scheduler", "runtime", "policy", "src"}
    for path in (LOCAL_TOOL, QDRANT_TOOL):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".", 1)[0])
        assert sorted(imports & forbidden) == []


def test_0142_manifest_lists_operator_extensions_only() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tools/run_local_vector_indexing_live_smoke.py",
        "tools/run_qdrant_projection_live_smoke.py",
        "tests/tools/test_machine_vector_handoff_0142.py",
        "tests/rules/test_machine_vector_handoff_0142_rule.py",
        "doc/architecture/MACHINE_VECTOR_HANDOFF_0142.md",
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
