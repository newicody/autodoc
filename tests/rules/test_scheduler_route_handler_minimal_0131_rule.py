from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "scheduler_route_handler_minimal.py"
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_ROUTE_HANDLER_MINIMAL_0131.md"
RULE = ROOT / "doc" / "code-rules" / "0131_scheduler_route_handler_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0131_CHANGED_FILES.md"


def test_0131_docs_and_rule_lock_handler_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    required = [
        "SchedulerRouteHandler is an executor bridge, not an orchestrator",
        "Scheduler remains the orchestrator",
        "Do not modify Scheduler.run() in 0131",
        "RouteProxyRuntime performs the /dev/shm IO",
        "EventBus receives observation-ready facts, not payload commands",
        "SQLContextStore remains durable authority",
        "E5/OpenVINO and Qdrant are not touched by 0131",
        "code_rule supplement for Scheduler route handler membrane",
    ]
    for phrase in required:
        assert phrase in text or phrase in rule


def test_0131_manifest_lists_docs_runtime_tests_and_rule_supplement() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/runtime/scheduler_route_handler_minimal.py",
        "tests/runtime/test_scheduler_route_handler_minimal.py",
        "tests/rules/test_scheduler_route_handler_minimal_0131_rule.py",
        "doc/architecture/SCHEDULER_ROUTE_HANDLER_MINIMAL_0131.md",
        "doc/code-rules/0131_scheduler_route_handler_rule.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
        "src/observability/event_bus.py",
        "requests",
        "httpx",
        "openvino.runtime",
        "qdrant_client",
        "psycopg",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0131_runtime_module_has_no_unapproved_imports() -> None:
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


def test_0131_module_does_not_become_scheduler_or_policy() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = [
        "Scheduler(",
        "Scheduler.run(",
        "Dispatcher(",
        "PolicyEngine(",
        "PriorityQueue(",
        "EventType(",
        "LocalServerOrchestrator",
        "qdrant_client",
        "openvino.runtime",
        "requests.",
    ]
    for phrase in forbidden:
        assert phrase not in text
    required = [
        "0131 is the first handler-shaped bridge",
        "It does not mutate the Scheduler run loop",
        '"scheduler_is_orchestrator": True',
        '"handler_is_executor": True',
        '"scheduler_run_modified": False',
        '"event_bus_observation_only": True',
        '"dev_shm_data_plane": True',
    ]
    for phrase in required:
        assert phrase in text
