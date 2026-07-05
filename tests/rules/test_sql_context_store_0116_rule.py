from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "sql_context_store.py"
DOC = ROOT / "doc" / "architecture" / "SQL_CONTEXT_STORE_0116.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0116_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "109_sql_context_store_minimal.dot"


def test_0116_documents_sql_authority_and_local_install_layout() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "SQLContextStore is durable context authority",
        "active PostgreSQL lives on fast_pool",
        "data_pool receives ZFS snapshots and backups",
        "Qdrant is vector projection and retrieval, not context authority",
        "OpenVINO produces local embeddings behind an adapter",
        "Scheduler orchestrates context exploration jobs; it does not build variants itself",
        "No PostgreSQL/Qdrant/OpenVINO/LLM runtime import in Scheduler",
    ]
    for phrase in required:
        assert phrase in text


def test_0116_manifest_does_not_touch_kernel_or_route_runtime() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/sql_context_store.py",
        "tests/runtime/test_sql_context_store_minimal.py",
        "tests/rules/test_sql_context_store_0116_rule.py",
        "doc/architecture/SQL_CONTEXT_STORE_0116.md",
        "doc/docs/architecture/runtime/109_sql_context_store_minimal.dot",
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


def test_0116_module_uses_only_stdlib_and_no_backend_runtime_imports() -> None:
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
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "src.kernel",
        "src.runtime",
        "src.policy",
    }
    assert sorted(imports & forbidden) == []


def test_0116_graph_shows_sql_authority_not_projection() -> None:
    text = DOT.read_text(encoding="utf-8")
    required = [
        "SourceCandidate",
        "SQLContextStore",
        "fast_pool active PostgreSQL",
        "data_pool ZFS snapshots",
        "Qdrant projection",
        "OpenVINO adapter",
        "InferenceContext",
    ]
    for phrase in required:
        assert phrase in text
