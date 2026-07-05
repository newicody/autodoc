from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "vector_indexing_job_plan.py"
DOC = ROOT / "doc" / "architecture" / "VECTOR_INDEXING_JOB_PLAN_0128.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0128_CHANGED_FILES.md"


def test_0128_documents_scheduler_vector_indexing_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "VectorIndexingJobPlan schedules E5/OpenVINO embedding and Qdrant projection without executing either",
        "Scheduler remains the orchestrator of vector indexing jobs",
        "route /dev/shm is the multitask data-plane interface and future grid seam",
        "SQLContextStore is durable context authority",
        "E5/OpenVINO remains embedding only behind adapter",
        "Qdrant is projection and recall only; it does not decide",
        "one Qdrant instance with role-oriented collections, not per-specialist databases",
        "EventBus observes vector indexing statistics and paths, not payloads",
        "GitHub exchanges artifacts only",
        "Specialist identity stays payload/filter metadata",
    ]
    for phrase in required:
        assert phrase in text


def test_0128_manifest_does_not_touch_kernel_or_runtime_clients() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/vector_indexing_job_plan.py",
        "tests/runtime/test_vector_indexing_job_plan.py",
        "tests/rules/test_vector_indexing_job_plan_0128_rule.py",
        "doc/architecture/VECTOR_INDEXING_JOB_PLAN_0128.md",
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


def test_0128_module_has_no_runtime_imports() -> None:
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


def test_0128_module_locks_plan_not_parallel_orchestrator() -> None:
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
        "LocalServerOrchestrator",
    ]
    for phrase in forbidden:
        assert phrase not in text
    required = [
        "Scheduler remains the orchestrator of vector indexing jobs",
        "route /dev/shm is the multitask data-plane interface and future grid seam",
        '"scheduler_is_orchestrator": True',
        '"parallel_local_orchestrator": False',
        '"e5_openvino_role": "embedding only behind adapter"',
        '"qdrant_role": "projection and recall only"',
        '"qdrant_decides": False',
        '"route_dev_shm_multitask_interface": True',
    ]
    for phrase in required:
        assert phrase in text
