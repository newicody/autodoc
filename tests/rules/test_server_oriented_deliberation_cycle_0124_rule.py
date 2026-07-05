from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "server_oriented_deliberation_cycle.py"
DOC = ROOT / "doc" / "architecture" / "SERVER_ORIENTED_DELIBERATION_CYCLE_0124.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0124_CHANGED_FILES.md"


def test_0124_documents_github_as_artifact_exchange_only_and_local_deliberation() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "GitHub artifact exchange only moves artifacts in and final artifacts out",
        "ServerOrientation drives specialist deliberation before publication",
        "Specialist preliminary opinions are recomposed into refined demands",
        "Specialist bus statistics feed passive supervision and VisPy, not GitHub",
        "Final GitHub publication happens only after local convergence",
        "Specialist proposals may be accepted as analysis signals without being validated as final solutions",
        "The server may ask for context influence, review, validation, or another specialist before production",
        "SQLContextStore is durable context authority",
        "Qdrant is vector projection and retrieval, not context authority",
        "OpenVINO produces embeddings behind adapter",
        "LLM is specialist producer, not context authority",
    ]
    for phrase in required:
        assert phrase in text


def test_0124_manifest_does_not_touch_kernel_or_add_runtime_clients() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/server_oriented_deliberation_cycle.py",
        "tests/runtime/test_server_oriented_deliberation_cycle.py",
        "tests/rules/test_server_oriented_deliberation_cycle_0124_rule.py",
        "doc/architecture/SERVER_ORIENTED_DELIBERATION_CYCLE_0124.md",
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
        "src/context/github_publication_review.py",
        "doc/docs/architecture/runtime/116_github_publication_review.dot",
        "vispy",
        "requests",
        "socket",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0124_module_has_no_unapproved_runtime_imports() -> None:
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
        "src.kernel",
        "src.runtime",
        "src.policy",
    }
    assert sorted(imports & forbidden) == []


def test_0124_module_keeps_publication_and_visualization_boundaries() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = [
        "EventType(",
        "Scheduler(",
        "Dispatcher(",
        "PolicyEngine(",
        "PriorityQueue(",
        "GitHubPublicationReview",
        "VisPy(",
        "requests.",
        "socket.",
    ]
    for phrase in forbidden:
        assert phrase not in text
    required = [
        "GitHub artifact exchange only moves artifacts in and final artifacts out.",
        "Specialist bus statistics feed passive supervision and VisPy, not GitHub.",
        '"publish_to_github": False',
        '"contains_internal_bus_statistics": False',
    ]
    for phrase in required:
        assert phrase in text
