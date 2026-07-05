from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "vector_contract_indexing_plan.py"
DOC = ROOT / "doc" / "architecture" / "VECTOR_CONTRACT_INDEXING_PLAN_0126.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0126_CHANGED_FILES.md"


def test_0126_documents_vector_contract_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "One Qdrant instance, multiple role-oriented collections",
        "Do not create one Qdrant database per specialist in 0126",
        "contracts_e5_384",
        "specialist_outputs_e5_384",
        "deliberation_signals_e5_384",
        "synthesis_candidates_e5_384",
        "E5/OpenVINO indexes contracts and specialist outputs behind adapter",
        "Qdrant links context, contracts, opinions, signals, and synthesis candidates; it does not decide",
        "Scheduler remains the orchestrator of deliberation",
        "SQLContextStore is durable context authority",
        "GitHub exchanges artifacts only",
        "Specialists produce machine_result plus human_representation",
    ]
    for phrase in required:
        assert phrase in text


def test_0126_manifest_does_not_touch_kernel_or_runtime_clients() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/vector_contract_indexing_plan.py",
        "tests/runtime/test_vector_contract_indexing_plan.py",
        "tests/rules/test_vector_contract_indexing_plan_0126_rule.py",
        "doc/architecture/VECTOR_CONTRACT_INDEXING_PLAN_0126.md",
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


def test_0126_module_has_no_unapproved_runtime_imports() -> None:
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


def test_0126_module_locks_collection_roles_and_embedding_only() -> None:
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
        "Qdrant stores projection collections by role, not one database per specialist.",
        '"per_specialist_database": False',
        '"qdrant_role": "projection only"',
        '"sql_is_authority": True',
        '"e5_openvino_role": "embedding only behind adapter"',
        '"qdrant_decides": False',
        '"scheduler_orchestrates": True',
        '"specialist_receives_machine_and_human_contracts": True',
    ]
    for phrase in required:
        assert phrase in text
