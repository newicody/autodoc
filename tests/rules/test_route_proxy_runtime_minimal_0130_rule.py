from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "route_proxy_runtime_minimal.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_PROXY_RUNTIME_MINIMAL_0130.md"
RULE = ROOT / "doc" / "code-rules" / "0130_route_proxy_runtime_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0130_CHANGED_FILES.md"


def test_0130_docs_and_rule_lock_runtime_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    required = [
        "RouteProxy runtime is a data-plane executor, not an orchestrator",
        "Scheduler remains the orchestrator",
        "Do not modify Scheduler.run() in 0130",
        "No mount table scan is allowed",
        "EventBus receives observation-ready facts, not payload commands",
        "SQLContextStore remains durable authority",
        "E5/OpenVINO and Qdrant are not touched by 0130",
        "documentation architecture is updated in this patch",
        "code_rule supplement for RouteProxy runtime membrane",
    ]
    for phrase in required:
        assert phrase in text or phrase in rule


def test_0130_manifest_lists_docs_runtime_tests_and_code_rule_supplement() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/runtime/route_proxy_runtime_minimal.py",
        "tests/runtime/test_route_proxy_runtime_minimal.py",
        "tests/rules/test_route_proxy_runtime_minimal_0130_rule.py",
        "doc/architecture/ROUTE_PROXY_RUNTIME_MINIMAL_0130.md",
        "doc/code-rules/0130_route_proxy_runtime_rule.md",
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


def test_0130_runtime_module_has_no_unapproved_imports() -> None:
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


def test_0130_runtime_module_does_not_become_scheduler_or_event_bus() -> None:
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
        "no mount scan",
        '"mount_scan": False',
        '"daemon": False',
        '"scheduler_is_orchestrator": True',
        '"route_proxy_is_fast_data_plane_control": True',
        '"event_bus_role": "observation_only"',
        '"payload_command": False',
    ]
    for phrase in required:
        assert phrase in text
