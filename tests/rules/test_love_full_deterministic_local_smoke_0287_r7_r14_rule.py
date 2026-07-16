from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_full_deterministic_local_smoke_0287.py"
REPORT = ROOT / "PHASE0287_R7_R14_FULL_DETERMINISTIC_LOCAL_SMOKE_REPORT.md"
ARCH = ROOT / "doc/architecture/FULL_DETERMINISTIC_LOCAL_SMOKE_0287_R7_R14.md"
DOT = ROOT / "doc/architecture/FULL_DETERMINISTIC_LOCAL_SMOKE_0287_R7_R14.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R14_FULL_DETERMINISTIC_LOCAL_SMOKE.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R14_FULL_DETERMINISTIC_LOCAL_SMOKE.md"


def test_r14_bundle_is_complete_and_dot_remains_source_only() -> None:
    for path in (SOURCE, REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
    assert not DOT.with_suffix(".svg").exists()


def test_smoke_composes_canonical_r7_r11_r12_r13_surfaces() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for token in (
        "github_dual_artifact_run_assembly_0281",
        "correlated_research_work_package_0287",
        "apply_source_candidate_decision",
        "submit_native_love_collaboration_visit",
        "run_love_memory_evidence_liaison_synthesis",
        "plan_love_final_deliverable_publication",
        "verify_love_final_deliverable_publication_readback",
    ):
        assert token in text


def test_smoke_creates_no_parallel_runtime_or_network_client() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import subprocess",
        "class LaboratoryManager",
        "class MemoryManager",
        "class PublicationManager",
        "class Scheduler",
        "class Orchestrator",
        "QdrantClient(",
        "openvino.runtime",
    )
    for token in forbidden:
        assert token not in text


def test_smoke_requires_same_scheduler_operator_gate_and_closed_remote_boundary() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for token in (
        "explicit_operator_gate_used",
        "same_scheduler_used",
        "remote_mutation_allowed",
        "remote_mutation_performed",
        "three_artifacts_assembled",
        "openvino_e5_384_reused",
    ):
        assert token in text


def test_dot_contains_architecture_only_and_no_policy_document_reference() -> None:
    text = DOT.read_text(encoding="utf-8")
    assert "code_rule" not in text.lower()
    assert "Scheduler" in text
    assert "SQL" in text
    assert "Qdrant" in text
    assert "ProjectV2" in text


def test_manifest_declares_next_real_closed_loop_phase() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    for token in (
        "Scheduler reused",
        "SQL authority exercised",
        "Qdrant projection/recall exercised",
        "GitHub mutation not performed",
        "0287-r7-r15",
    ):
        assert token in text
