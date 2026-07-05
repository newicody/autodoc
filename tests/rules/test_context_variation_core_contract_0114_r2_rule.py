from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/context_variation_core.py"
DOC = ROOT / "doc/architecture/CONTEXT_VARIATION_CORE_CONTRACT_0114_R2.md"
DOT = ROOT / "doc/docs/architecture/runtime/107_context_variation_core_contract.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0114_R2_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0114_r2_locks_context_variability_center() -> None:
    text = _read(MODULE) + "\n" + _read(DOC)
    required = [
        "context variability is the project center",
        "ContextVariationObjective",
        "ContextVariationAxis",
        "ContextTrajectory",
        "ContextVariantCandidate",
        "ContextExplorationPlan",
        "InferenceContextDraft",
        "MVTC remains future, not runtime in 0114-r2",
        "Scheduler orchestrates context exploration jobs; it does not build variants itself",
        "SQLContextStore is durable context authority",
        "Qdrant is vector projection and retrieval, not context authority",
        "OpenVINO produces local embeddings or light inference behind an adapter",
        "LLM consumes InferenceContextDraft or InferenceContext through specialist boundary",
    ]
    for phrase in required:
        assert phrase in text


def test_0114_r2_forbids_backend_imports_and_kernel_edits() -> None:
    text = _read(MODULE)
    forbidden = [
        "import sqlite3",
        "import qdrant",
        "from qdrant",
        "openvino",
        "OpenVINO",
        "import requests",
        "import httpx",
        "import socket",
        "EventType(",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0114_r2_graph_is_context_centered() -> None:
    dot = _read(DOT)
    required = [
        "ROOT_GRAPH: doc/docs/architecture/00_global.dot",
        "root-attached context overlay",
        "ContextVariationObjective -> ContextExplorationPlan -> ContextVariantCandidate -> ContextTrajectory -> ContextExplorationResult -> InferenceContextDraft",
        "SQLContextStore is durable context authority",
        "Qdrant is vector projection and retrieval, not context authority",
        "OpenVINO produces local embeddings or light inference behind an adapter",
        "LLM consumes InferenceContextDraft or InferenceContext through specialist boundary",
        "MVTC remains future, not runtime in 0114-r2",
    ]
    for phrase in required:
        assert phrase in dot


def test_0114_r2_manifest_does_not_touch_kernel_loop() -> None:
    manifest = _read(MANIFEST)
    assert "src/context/context_variation_core.py" in manifest
    assert "tests/runtime/test_context_variation_core_contract.py" in manifest
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/kernel/dispatcher.py" not in manifest
    assert "src/kernel/queue.py" not in manifest
    assert "src/policy/engine.py" not in manifest
    assert "src/kernel/event_bus.py" not in manifest
