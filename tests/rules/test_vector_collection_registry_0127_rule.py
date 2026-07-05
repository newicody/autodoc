from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "vector_collection_registry.py"
DOC = ROOT / "doc" / "architecture" / "VECTOR_COLLECTION_REGISTRY_0127.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0127_CHANGED_FILES.md"


def test_0127_documents_registry_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "VectorCollectionRegistry turns 0126 roles into a local collection registry",
        "One Qdrant instance, multiple role-oriented collections",
        "Do not create one Qdrant database per specialist in 0127",
        "adapter executes collection creation later",
        "Scheduler remains the orchestrator of deliberation",
        "SQLContextStore is durable context authority",
        "E5/OpenVINO remains embedding only behind adapter",
        "Qdrant is projection and recall only; it does not decide",
        "GitHub exchanges artifacts only",
        "EventBus observes statistics and paths, not payloads",
        "route /dev/shm remains multitask data-plane interface",
    ]
    for phrase in required:
        assert phrase in text


def test_0127_manifest_does_not_touch_kernel_or_runtime_clients() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/vector_collection_registry.py",
        "tests/runtime/test_vector_collection_registry.py",
        "tests/rules/test_vector_collection_registry_0127_rule.py",
        "doc/architecture/VECTOR_COLLECTION_REGISTRY_0127.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
        "src/observability/event_bus.py",
        "src/runtime/route_runtime_manager.py",
        "requests",
        "socket",
        "openvino.runtime",
        "qdrant_client",
        "psycopg",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0127_module_has_no_runtime_imports() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = {
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "openvino",
        "qdrant",
        "qdrant_client",
        "psycopg",
        "sqlite3",
        "graphviz",
        "networkx",
        "vispy",
        "src",
    }
    assert sorted(imports & forbidden) == []


def test_0127_module_locks_registry_not_orchestrator() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = [
        "Scheduler(",
        "Scheduler.run(",
        "Dispatcher(",
        "PolicyEngine(",
        "PriorityQueue(",
        "EventType(",
        "qdrant_client",
        "openvino.runtime",
        "requests.",
        "socket.",
        "per_specialist_database = True",
    ]
    for phrase in forbidden:
        assert phrase not in text
    required = [
        "One Qdrant instance owns multiple role-oriented collections",
        '"one_qdrant_instance_multiple_role_collections": True',
        '"per_specialist_database": False',
        '"scheduler_orchestrates": True',
        '"e5_openvino_role": "embedding only behind adapter"',
        '"qdrant_role": "projection and recall only"',
        '"adapter_executes_later": True',
        '"qdrant_decides": False',
    ]
    for phrase in required:
        assert phrase in text
