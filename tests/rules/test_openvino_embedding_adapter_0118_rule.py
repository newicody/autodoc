from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "inference" / "openvino_embedding_adapter.py"
DOC = ROOT / "doc" / "architecture" / "OPENVINO_EMBEDDING_ADAPTER_0118.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0118_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "111_openvino_embedding_adapter.dot"


def test_0118_documents_openvino_embedding_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "OpenVINOEmbeddingAdapter builds bounded embedding requests from hydrated SQL fragments",
        "SQLContextStore is durable context authority",
        "SQLContextHydrator converts sql:* refs into lightweight hydrated context fragments",
        "OpenVINO is a specialist embedding backend behind src/inference/openvino_runtime.py",
        "Qdrant is vector projection and retrieval, not context authority",
        "Scheduler orchestrates context exploration jobs; it does not build variants itself",
        "No Qdrant/PostgreSQL/LLM runtime import in OpenVINOEmbeddingAdapter",
        "MVTC remains future, not runtime in 0118",
    ]
    for phrase in required:
        assert phrase in text


def test_0118_manifest_does_not_touch_kernel_or_runtime_authority() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/inference/openvino_embedding_adapter.py",
        "tests/runtime/test_openvino_embedding_adapter.py",
        "tests/rules/test_openvino_embedding_adapter_0118_rule.py",
        "doc/architecture/OPENVINO_EMBEDDING_ADAPTER_0118.md",
        "doc/docs/architecture/runtime/111_openvino_embedding_adapter.dot",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
        "src/runtime/route_runtime_manager.py",
        "src/observability/event_bus.py",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0118_module_has_no_unapproved_backend_runtime_imports() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = {
        "openvino",
        "qdrant",
        "psycopg",
        "sqlite3",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "src.kernel",
        "src.runtime",
        "src.policy",
    }
    assert sorted(imports & forbidden) == []


def test_0118_module_does_not_create_events_or_scheduler_commands() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = ["EventType(", "Scheduler(", "Dispatcher(", "PolicyEngine(", "PriorityQueue("]
    for phrase in forbidden:
        assert phrase not in text


def test_0118_graph_shows_embedding_before_qdrant_projection() -> None:
    text = DOT.read_text(encoding="utf-8")
    required = [
        "SQLContextHydrator",
        "Hydrated SQL fragments",
        "OpenVINOEmbeddingAdapter",
        "src/inference/openvino_runtime.py",
        "Embedding vectors",
        "Qdrant projection adapter later",
        "InferenceContextDraft",
    ]
    for phrase in required:
        assert phrase in text
