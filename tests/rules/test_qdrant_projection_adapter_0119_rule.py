from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "inference" / "qdrant_projection_adapter.py"
DOC = ROOT / "doc" / "architecture" / "QDRANT_PROJECTION_ADAPTER_0119.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0119_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "112_qdrant_projection_adapter.dot"


def test_0119_documents_qdrant_projection_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "QdrantProjectionAdapter projects embedding vectors into Qdrant-ready points",
        "SQLContextStore is durable context authority",
        "Qdrant is vector projection and retrieval, not context authority",
        "Qdrant payload carries sql_context_ref for SQL re-hydration",
        "No qdrant-client/PostgreSQL/OpenVINO/LLM runtime import in QdrantProjectionAdapter",
        "Scheduler orchestrates context exploration jobs; it does not build variants itself",
        "MVTC remains future, not runtime in 0119",
    ]
    for phrase in required:
        assert phrase in text


def test_0119_manifest_does_not_touch_kernel_or_runtime_authority() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/inference/qdrant_projection_adapter.py",
        "tests/runtime/test_qdrant_projection_adapter.py",
        "tests/rules/test_qdrant_projection_adapter_0119_rule.py",
        "doc/architecture/QDRANT_PROJECTION_ADAPTER_0119.md",
        "doc/docs/architecture/runtime/112_qdrant_projection_adapter.dot",
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


def test_0119_module_has_no_unapproved_backend_runtime_imports() -> None:
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


def test_0119_module_does_not_create_events_or_scheduler_commands() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = ["EventType(", "Scheduler(", "Dispatcher(", "PolicyEngine(", "PriorityQueue("]
    for phrase in forbidden:
        assert phrase not in text


def test_0119_graph_shows_qdrant_projection_then_sql_rehydration() -> None:
    text = DOT.read_text(encoding="utf-8")
    required = [
        "OpenVINOEmbeddingAdapter",
        "Embedding vectors",
        "QdrantProjectionAdapter",
        "Qdrant-ready points",
        "Qdrant recall hits",
        "sql_context_ref",
        "SQLContextHydrator re-hydrates refs",
        "InferenceContextDraft",
    ]
    for phrase in required:
        assert phrase in text
