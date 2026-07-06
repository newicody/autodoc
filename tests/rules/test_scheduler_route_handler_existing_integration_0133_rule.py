from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "scheduler_route_handler_minimal.py"
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_ROUTE_HANDLER_EXISTING_INTEGRATION_0133.md"
RULE = ROOT / "doc" / "code-rules" / "0133_extend_existing_runtime_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0133_CHANGED_FILES.md"


def test_0133_docs_lock_extend_existing_route_handler_decision() -> None:
    text = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    required = [
        "0133 extends existing scheduler_route_handler_minimal.py",
        "Do not create fake_specialist_worker_minimal.py in 0133",
        "Do not create a new route handler or runtime wheel when audited surfaces exist",
        "Scheduler remains the orchestrator",
        "RouteProxyRuntime remains the IO executor",
        "Scheduler.run() is not modified",
        "EventBus receives observation-ready facts only",
        "OpenVINO and Qdrant remain out of this handler patch",
        "0132 audit decision: reuse_or_extend_existing",
    ]
    for phrase in required:
        assert phrase in text or phrase in rule


def test_0133_manifest_modifies_existing_handler_not_new_runtime_module() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/runtime/scheduler_route_handler_minimal.py",
        "tests/runtime/test_scheduler_route_handler_minimal.py",
        "tests/rules/test_scheduler_route_handler_existing_integration_0133_rule.py",
        "doc/architecture/SCHEDULER_ROUTE_HANDLER_EXISTING_INTEGRATION_0133.md",
        "doc/code-rules/0133_extend_existing_runtime_rule.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/runtime/fake_specialist_worker_minimal.py",
        "src/runtime/scheduler_route_handler_existing_integration.py",
        "src/runtime/new_scheduler_route_handler.py",
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


def test_0133_handler_module_has_no_unapproved_imports() -> None:
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


def test_0133_module_locks_existing_integration_not_parallel_runtime() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = [
        "Scheduler(",
        "Scheduler.run(",
        "Dispatcher(",
        "PolicyEngine(",
        "PriorityQueue(",
        "EventType(",
        "LocalServerOrchestrator",
        "FakeSpecialistWorker",
        "fake_specialist_worker_minimal",
        "qdrant_client",
        "openvino.runtime",
        "requests.",
    ]
    for phrase in forbidden:
        assert phrase not in text
    required = [
        "ExistingRouteHandlerIntegrationDecision",
        "describe_existing_scheduler_route_handler_integration",
        "extends_existing_scheduler_route_handler",
        '"creates_parallel_runtime": False',
        '"decision": "extend_existing"',
        '"scheduler_run_modified": False',
        "src/runtime/scheduler_route_handler_minimal.py",
        "src/runtime/route_proxy_runtime_minimal.py",
    ]
    for phrase in required:
        assert phrase in text
