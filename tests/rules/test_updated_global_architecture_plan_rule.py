from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_updated_architecture_reframes_event_rule_correctly() -> None:
    doc = _read("doc/architecture/UPDATED_GLOBAL_ARCHITECTURE_PLAN_AFTER_CONTEXT_QDRANT_MVTC.md")
    assert "no event-to-action shortcut" in doc
    assert "Events may feed the existing intent system" in doc
    assert "Only validated typed commands may reach the Scheduler" in doc


def test_updated_architecture_restores_mvtc_context_variation_role() -> None:
    doc = _read("doc/architecture/UPDATED_GLOBAL_ARCHITECTURE_PLAN_AFTER_CONTEXT_QDRANT_MVTC.md")
    assert "MVTC is a context variation and testing engine" in doc
    assert "RiskSignal" in doc
    assert "risk policy is only one output of MVTC" in doc


def test_updated_architecture_defines_qdrant_as_projection_memory() -> None:
    doc = _read("doc/architecture/UPDATED_GLOBAL_ARCHITECTURE_PLAN_AFTER_CONTEXT_QDRANT_MVTC.md")
    assert "Qdrant is vector memory and similarity search" in doc
    assert "qdrant_core" in doc
    assert "qdrant_work" in doc
    assert "qdrant_lab" in doc
    assert "Qdrant stores projections" in doc


def test_baby_fork_example_uses_context_gate_and_domain_filtering() -> None:
    doc = _read("doc/architecture/FORK_FOR_BABY_EXAMPLE_NEXT_ARCHITECTURE.md")
    assert "baby fork" in doc
    assert "food_contact=true" in doc
    assert "ContextGate" in doc
    assert "MVTC creates and compares context variants" in doc
    assert "LanguageModelWorker" in doc


def test_next_development_line_contains_context_qdrant_mvtc_phases() -> None:
    doc = _read("doc/architecture/NEXT_DEVELOPMENT_LINE_R2.md")
    assert "Phase 12 — Context runtime" in doc
    assert "Phase 14 — Qdrant runtime" in doc
    assert "Phase 15 — MVTC runtime" in doc
    assert "LanguageModelWorker boundary" in doc


def test_updated_plan_manifest_has_no_runtime_changes() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART11_2_R2_RUNTIME_TOKEN_ZONE_CONTEXT_QDRANT_PLAN.md")
    assert "Runtime changes" in manifest
    assert "None" in manifest
    assert "requirements" not in manifest
    assert ".svg" not in manifest
