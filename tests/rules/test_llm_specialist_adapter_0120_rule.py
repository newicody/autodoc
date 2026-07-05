from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "inference" / "llm_specialist_adapter.py"
DOC = ROOT / "doc" / "architecture" / "LLM_SPECIALIST_ADAPTER_0120.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0120_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "113_llm_specialist_adapter.dot"


def test_0120_documents_llm_specialist_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "LLMSpecialistAdapter consumes InferenceContextDraft and hydrated SQL fragments",
        "LLM is specialist producer, not context authority",
        "SQLContextStore is durable context authority",
        "Qdrant is vector projection and retrieval, not context authority",
        "No LLM SDK/HTTP/socket/Qdrant/OpenVINO/PostgreSQL runtime import in LLMSpecialistAdapter",
        "Scheduler orchestrates context exploration jobs; it does not build variants itself",
        "MVTC remains future, not runtime in 0120",
    ]
    for phrase in required:
        assert phrase in text


def test_0120_manifest_does_not_touch_kernel_or_runtime_authority() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/inference/llm_specialist_adapter.py",
        "tests/runtime/test_llm_specialist_adapter.py",
        "tests/rules/test_llm_specialist_adapter_0120_rule.py",
        "doc/architecture/LLM_SPECIALIST_ADAPTER_0120.md",
        "doc/docs/architecture/runtime/113_llm_specialist_adapter.dot",
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


def test_0120_module_has_no_unapproved_backend_runtime_imports() -> None:
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
        "sqlite3",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "llama_cpp",
        "transformers",
        "src.kernel",
        "src.runtime",
        "src.policy",
    }
    assert sorted(imports & forbidden) == []


def test_0120_module_does_not_create_events_or_scheduler_commands() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = ["EventType(", "Scheduler(", "Dispatcher(", "PolicyEngine(", "PriorityQueue("]
    for phrase in forbidden:
        assert phrase not in text


def test_0120_graph_shows_specialist_after_sql_rehydration() -> None:
    text = DOT.read_text(encoding="utf-8")
    required = [
        "InferenceContextDraft",
        "SQLContextHydrator",
        "Hydrated SQL fragments",
        "LLMSpecialistAdapter",
        "Injected LLM executor",
        "Solution candidates",
        "evidence_refs",
        "GitHub project result later",
    ]
    for phrase in required:
        assert phrase in text
