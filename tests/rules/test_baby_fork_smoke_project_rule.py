from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_baby_fork_smoke_project_declares_real_minimal_flow() -> None:
    source = _read("src/context/baby_fork_smoke_project.py")
    assert 'BABY_FORK_SMOKE_PROJECT_SCHEMA = "missipy.baby_fork_smoke_project.v1"' in source
    assert "retrieve_baby_fork_documents" in source
    assert "make_two_baby_fork_variants_stub" in source
    assert "apply_baby_fork_context_patch" in source
    assert "run_baby_fork_smoke_project" in source


def test_baby_fork_smoke_project_retrieval_replaces_calculation_for_single_domain() -> None:
    doc = _read("doc/smoke/BABY_FORK_CONTEXT_SMOKE_PROJECT.md")
    assert "retrieval replaces calculation for this single domain first" in doc
    assert "one RetrievalWorker" in doc
    assert "two VariantGeneratorStub variants" in doc
    assert "ContextGate" in doc
    assert "cell-lens is fed by this real flow, not the synthetic generator" in doc


def test_baby_fork_smoke_project_has_no_qdrant_dependency_yet() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART12_1_BABY_FORK_SMOKE_PROJECT_CONTEXT_FLOW.md")
    assert "stand-in stdlib retrieval" in manifest
    assert "qdrant dependency" not in manifest
    assert ".svg" not in manifest
