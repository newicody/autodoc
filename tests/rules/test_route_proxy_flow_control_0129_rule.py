from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "route_proxy_flow_control_contract.py"
DOC = ROOT / "doc" / "architecture" / "ROUTE_PROXY_FLOW_CONTROL_CONTRACT_0129.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0129_CHANGED_FILES.md"


def test_0129_docs_lock_route_proxy_scheduler_dev_shm_bus_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "RouteProxy is fast data-plane flow control, not an orchestrator",
        "Scheduler remains the orchestrator",
        "/dev/shm route zones are a multitask interface and future grid seam",
        "RouteProxy can reserve, block, stale, and reprioritize route zones quickly",
        "EventBus receives observation facts and statistics, not payload commands",
        "RouteProxy registry snapshots are runtime mirrors, not durable authority",
        "SQLContextStore remains durable context authority",
        "E5/OpenVINO remains embedding only behind adapter",
        "Qdrant remains projection and recall only",
        "Do not modify Scheduler.run() in 0129",
    ]
    for phrase in required:
        assert phrase in text


def test_0129_manifest_does_not_touch_kernel_or_add_runtime_clients() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/route_proxy_flow_control_contract.py",
        "tests/runtime/test_route_proxy_flow_control_contract.py",
        "tests/rules/test_route_proxy_flow_control_0129_rule.py",
        "doc/architecture/ROUTE_PROXY_FLOW_CONTROL_CONTRACT_0129.md",
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
        "httpx",
        "socket",
        "vispy",
        "qdrant_client",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0129_module_has_no_unapproved_runtime_imports() -> None:
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


def test_0129_module_locks_proxy_as_data_plane_not_policy_or_scheduler() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = [
        "Scheduler(",
        "Scheduler.run(",
        "Dispatcher(",
        "PolicyEngine(",
        "PriorityQueue(",
        "EventType(",
        "GitHubPublicationReview",
        "LocalServerOrchestrator",
        "requests.",
        "socket.",
    ]
    for phrase in forbidden:
        assert phrase not in text
    required = [
        "RouteProxy flow control as a fast data-plane guard",
        "Scheduler remains the orchestrator",
        "/dev/shm route zones",
        '"route_proxy_role": "fast_dev_shm_flow_control"',
        '"scheduler_remains_orchestrator": True',
        '"route_proxy_is_fast_data_plane_control": True',
        '"event_bus_observation_only": True',
        '"sql_is_durable_authority": True',
        '"dev_shm_future_grid_seam": True',
    ]
    for phrase in required:
        assert phrase in text
