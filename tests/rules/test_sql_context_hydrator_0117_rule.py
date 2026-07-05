from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "sql_context_hydrator.py"
DOC = ROOT / "doc" / "architecture" / "SQL_CONTEXT_HYDRATOR_0117.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0117_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "110_sql_context_hydrator.dot"


def test_0117_documents_sql_hydration_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "SQLContextHydrator converts sql:* refs into lightweight hydrated context fragments",
        "SQLContextStore is durable context authority",
        "active PostgreSQL lives on fast_pool",
        "data_pool receives ZFS snapshots and backups",
        "Qdrant is vector projection and retrieval, not context authority",
        "OpenVINO produces local embeddings behind an adapter",
        "Scheduler orchestrates context exploration jobs; it does not build variants itself",
        "No PostgreSQL/Qdrant/OpenVINO/LLM runtime import in SQLContextHydrator",
        "MVTC remains future, not runtime in 0117",
    ]
    for phrase in required:
        assert phrase in text


def test_0117_manifest_does_not_touch_kernel_or_runtime_authority() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/sql_context_hydrator.py",
        "tests/runtime/test_sql_context_hydrator.py",
        "tests/rules/test_sql_context_hydrator_0117_rule.py",
        "doc/architecture/SQL_CONTEXT_HYDRATOR_0117.md",
        "doc/docs/architecture/runtime/110_sql_context_hydrator.dot",
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


def test_0117_module_has_no_backend_runtime_imports() -> None:
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


def test_0117_module_does_not_create_events_or_scheduler_commands() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = ["EventType(", "Scheduler(", "Dispatcher(", "PolicyEngine(", "PriorityQueue("]
    for phrase in forbidden:
        assert phrase not in text


def test_0117_graph_shows_hydration_before_projection_and_specialists() -> None:
    text = DOT.read_text(encoding="utf-8")
    required = [
        "SQLContextStore",
        "SQLContextHydrator",
        "Hydrated fragments",
        "OpenVINO adapter",
        "Qdrant projection",
        "InferenceContextDraft",
        "specialist / LLM boundary",
    ]
    for phrase in required:
        assert phrase in text
