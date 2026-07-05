from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "github_project_scenario.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_PROJECT_SCENARIO_0121.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0121_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "114_github_project_scenario.dot"


def test_0121_documents_github_baby_fork_scenario_without_runtime_api() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "GitHub artifact -> SourceCandidate SQL -> ContextExplorationPlan -> LLMSpecialistResult -> GitHubProjectPublication",
        "No GitHub API/HTTP/socket runtime import in GitHubProjectScenario",
        "SQLContextStore is durable context authority",
        "Qdrant is vector projection and retrieval, not context authority",
        "OpenVINO produces embeddings behind adapter",
        "LLM is specialist producer, not context authority",
        "Scheduler orchestrates context exploration jobs; it does not build variants itself",
        "MVTC remains future, not runtime in 0121",
    ]
    for phrase in required:
        assert phrase in text


def test_0121_manifest_does_not_touch_kernel_or_runtime_authority() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/github_project_scenario.py",
        "tests/runtime/test_github_project_scenario.py",
        "tests/rules/test_github_project_scenario_0121_rule.py",
        "doc/architecture/GITHUB_PROJECT_SCENARIO_0121.md",
        "doc/docs/architecture/runtime/114_github_project_scenario.dot",
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


def test_0121_module_has_no_unapproved_github_or_backend_runtime_imports() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = {
        "github",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "openvino",
        "qdrant",
        "psycopg",
        "sqlite3",
        "llama_cpp",
        "transformers",
        "src.kernel",
        "src.runtime",
        "src.policy",
    }
    assert sorted(imports & forbidden) == []


def test_0121_module_does_not_create_events_or_scheduler_commands() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = ["EventType(", "Scheduler(", "Dispatcher(", "PolicyEngine(", "PriorityQueue("]
    for phrase in forbidden:
        assert phrase not in text


def test_0121_graph_shows_github_result_after_specialist_boundary() -> None:
    text = DOT.read_text(encoding="utf-8")
    required = [
        "GitHub artifact",
        "SourceCandidate SQL",
        "SQLContextStore authority",
        "ContextExplorationPlan",
        "LLMSpecialistResult",
        "GitHubProjectPublication",
        "Future GitHub adapter posts result",
    ]
    for phrase in required:
        assert phrase in text
