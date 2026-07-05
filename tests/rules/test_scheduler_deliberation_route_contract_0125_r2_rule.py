from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "scheduler_deliberation_route_contract.py"
DOC = ROOT / "doc" / "architecture" / "SCHEDULER_DELIBERATION_ROUTE_CONTRACT_0125_R2.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0125_R2_CHANGED_FILES.md"


def test_0125_r2_documents_scheduler_dev_shm_bus_and_embedding_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "Scheduler is the deliberation orchestrator",
        "No parallel local server orchestrator is introduced",
        "/dev/shm route frames are a multitask data-plane interface for local workers and a future grid",
        "EventBus observes facts, statistics, and paths, not payload commands",
        "GitHub exchanges artifacts only: artifact in and final artifact out",
        "E5/OpenVINO is embedding only behind adapter, not decision maker",
        "SQLContextStore is durable context authority",
        "Qdrant is vector projection and retrieval, not context authority",
        "Specialist proposals are receivable as analysis signals before final validation",
        "Do not modify Scheduler.run() in 0125-r2",
    ]
    for phrase in required:
        assert phrase in text


def test_0125_r2_manifest_does_not_touch_kernel_or_add_runtime_clients() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/scheduler_deliberation_route_contract.py",
        "tests/runtime/test_scheduler_deliberation_route_contract.py",
        "tests/rules/test_scheduler_deliberation_route_contract_0125_r2_rule.py",
        "doc/architecture/SCHEDULER_DELIBERATION_ROUTE_CONTRACT_0125_R2.md",
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
        "src/context/server_deliberation_orchestrator.py",
        "requests",
        "socket",
        "vispy",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0125_r2_module_has_no_unapproved_runtime_imports() -> None:
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
        "psycopg",
        "sqlite3",
        "graphviz",
        "networkx",
        "vispy",
        "src",
    }
    assert sorted(imports & forbidden) == []


def test_0125_r2_module_locks_no_parallel_orchestrator_and_no_runtime_scheduler_call() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = [
        "LocalServerOrchestrator",
        "server_deliberation_orchestrator",
        "Scheduler(",
        "Scheduler.run(",
        "Dispatcher(",
        "PolicyEngine(",
        "PriorityQueue(",
        "EventType(",
        "GitHubPublicationReview",
        "requests.",
        "socket.",
    ]
    for phrase in forbidden:
        assert phrase not in text
    required = [
        "Scheduler is the deliberation orchestrator.",
        "/dev/shm route frames are a",
        "E5/OpenVINO is embedding only behind adapter, not decision",
        '"scheduler_is_orchestrator": True',
        '"dev_shm_is_multitask_interface": True',
        '"event_bus_observation_only": True',
        '"e5_embedding_only": True',
    ]
    for phrase in required:
        assert phrase in text
