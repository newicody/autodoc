from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "github_publication_review.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_PUBLICATION_REVIEW_0123.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0123_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "116_github_publication_review.dot"


def test_0123_documents_local_review_before_external_github_posting() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "GitHub publication review is local and reviewable; it does not post to GitHub",
        "GitHubProjectPublication + ContextGraphSnapshot + DotGraphExport -> GitHubPublicationReviewPacket",
        "No GitHub API/HTTP/socket import in GitHubPublicationReview",
        "SQLContextStore is durable context authority",
        "Qdrant is vector projection and retrieval, not context authority",
        "OpenVINO produces embeddings behind adapter",
        "LLM is specialist producer, not context authority",
        "Scheduler orchestrates context exploration jobs; it does not publish reviews itself",
        "MVTC remains future, not runtime in 0123",
    ]
    for phrase in required:
        assert phrase in text


def test_0123_manifest_does_not_touch_kernel_runtime_or_real_github_client() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/github_publication_review.py",
        "tests/runtime/test_github_publication_review.py",
        "tests/rules/test_github_publication_review_0123_rule.py",
        "doc/architecture/GITHUB_PUBLICATION_REVIEW_0123.md",
        "doc/docs/architecture/runtime/116_github_publication_review.dot",
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
        "src/integrations/github_client.py",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0123_module_has_no_unapproved_external_runtime_imports() -> None:
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
        "urllib",
        "socket",
        "subprocess",
        "webbrowser",
        "openvino",
        "qdrant",
        "psycopg",
        "sqlite3",
        "github",
        "src.kernel",
        "src.runtime",
        "src.policy",
    }
    assert sorted(imports & forbidden) == []


def test_0123_module_does_not_create_events_or_scheduler_publication() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = ["EventType(", "EventBus", "Scheduler(", "Dispatcher(", "PolicyEngine(", "PriorityQueue("]
    for phrase in forbidden:
        assert phrase not in text


def test_0123_graph_shows_review_before_future_github_adapter() -> None:
    text = DOT.read_text(encoding="utf-8")
    required = [
        "GitHubProjectPublication",
        "ContextGraphSnapshot",
        "DotGraphExport",
        "GitHubPublicationReviewPacket",
        "local review only",
        "future GitHub adapter posts after approval",
        "No GitHub API call",
    ]
    for phrase in required:
        assert phrase in text
