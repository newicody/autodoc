from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "specialist_liaison_synthesis.py"
DOC = ROOT / "doc" / "architecture" / "SPECIALIST_LIAISON_SYNTHESIS_0123_R2.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0123_R2_CHANGED_FILES.md"


def test_0123_r2_documents_specialist_liaison_not_github_review() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "SpecialistLiaisonSynthesis unifies specialist work before any final publication",
        "Specialist path observations are bus-ready facts, not commands",
        "VisPy can represent specialist paths from bus observations later",
        "No GitHub/DOT publication review in 0123-r2",
        "End-user synthesis hides specialist provenance by default",
        "Specialists may request context influence, review, or validation without posting to GitHub directly",
        "SQLContextStore is durable context authority",
        "Qdrant is vector projection and retrieval, not context authority",
        "OpenVINO produces embeddings behind adapter",
        "LLM is specialist producer, not context authority",
    ]
    for phrase in required:
        assert phrase in text


def test_0123_r2_manifest_does_not_touch_kernel_or_add_github_publication_review() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/specialist_liaison_synthesis.py",
        "tests/runtime/test_specialist_liaison_synthesis.py",
        "tests/rules/test_specialist_liaison_synthesis_0123_r2_rule.py",
        "doc/architecture/SPECIALIST_LIAISON_SYNTHESIS_0123_R2.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/context/github_publication_review.py",
        "doc/docs/architecture/runtime/116_github_publication_review.dot",
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
        "src/runtime/route_runtime_manager.py",
        "src/observability/event_bus.py",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0123_r2_module_has_no_unapproved_runtime_imports() -> None:
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


def test_0123_r2_module_is_not_scheduler_or_live_bus_authority() -> None:
    text = MODULE.read_text(encoding="utf-8")
    forbidden = ["EventType(", "Scheduler(", "Dispatcher(", "PolicyEngine(", "PriorityQueue(", "GitHubPublicationReview"]
    for phrase in forbidden:
        assert phrase not in text
    required = [
        "Specialist path observations are bus-ready facts, not commands.",
        "No GitHub/DOT publication review in 0123-r2.",
    ]
    assert required[0] in text
    assert required[1] in text
    assert '"publication_surface": "none until final adapter"' in text
