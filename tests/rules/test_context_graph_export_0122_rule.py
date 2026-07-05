from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "context_graph_export.py"
DOC = ROOT / "doc" / "architecture" / "CONTEXT_GRAPH_EXPORT_0122.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0122_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "115_context_graph_export.dot"


def test_0122_documents_passive_context_graph_export() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "Passive context graph export reads contracts only; it does not observe live events",
        "GitHubProjectScenarioPacket -> ContextGraphSnapshot -> DOT export",
        "No watcher/service/EventBus subscription in ContextGraphExport",
        "SQLContextStore is durable context authority",
        "Qdrant is vector projection and retrieval, not context authority",
        "OpenVINO produces embeddings behind adapter",
        "LLM is specialist producer, not context authority",
        "Scheduler orchestrates context exploration jobs; it does not build graphs itself",
        "MVTC remains future, not runtime in 0122",
    ]
    for phrase in required:
        assert phrase in text


def test_0122_manifest_does_not_touch_kernel_or_runtime_authority() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/context_graph_export.py",
        "tests/runtime/test_context_graph_export.py",
        "tests/rules/test_context_graph_export_0122_rule.py",
        "doc/architecture/CONTEXT_GRAPH_EXPORT_0122.md",
        "doc/docs/architecture/runtime/115_context_graph_export.dot",
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


def test_0122_module_has_no_unapproved_runtime_or_visualization_imports() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = {
        "graphviz",
        "networkx",
        "vispy",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "openvino",
        "qdrant",
        "psycopg",
        "sqlite3",
        "src.kernel",
        "src.runtime",
        "src.policy",
    }
    assert sorted(imports & forbidden) == []


def test_0122_module_does_not_create_events_or_scheduler_commands() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = ["EventType(", "EventBus", "Scheduler(", "Dispatcher(", "PolicyEngine(", "PriorityQueue("]
    for phrase in forbidden:
        assert phrase not in text


def test_0122_graph_shows_passive_export_after_github_scenario() -> None:
    text = DOT.read_text(encoding="utf-8")
    required = [
        "GitHubProjectScenarioPacket",
        "ContextGraphSnapshot",
        "DOT export",
        "SQLContextStore authority",
        "Qdrant projection/retrieval",
        "LLMSpecialistResult",
        "No live EventBus observation",
    ]
    for phrase in required:
        assert phrase in text
