from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/love_memory_evidence_liaison_synthesis_0287.py"
REPORT = ROOT / "PHASE0287_R7_R12_LOVE_MEMORY_EVIDENCE_LIAISON_SYNTHESIS_REPORT.md"
ARCH = ROOT / "doc/architecture/LOVE_MEMORY_EVIDENCE_LIAISON_SYNTHESIS_0287_R7_R12.md"
DOT = ROOT / "doc/architecture/LOVE_MEMORY_EVIDENCE_LIAISON_SYNTHESIS_0287_R7_R12.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R12_LOVE_MEMORY_EVIDENCE_LIAISON_SYNTHESIS.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R12_LOVE_MEMORY_EVIDENCE_LIAISON_SYNTHESIS.md"


def test_r12_reuses_existing_authority_recall_and_liaison_surfaces() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for token in (
        "SQLiteContextRevisionAuthorityStore",
        "execute_hybrid_retrieval",
        "build_specialist_liaison_synthesis",
        "build_final_synthesis_packet",
        "FinalArtifactEnvelope",
        "dense_e5_v1",
        "dimension != 384",
        "SQL authority",
    ):
        assert token in source


def test_r12_does_not_create_parallel_runtime_or_backend() -> None:
    source = MODULE.read_text(encoding="utf-8")
    forbidden = (
        "from qdrant_client",
        "import qdrant_client",
        "from openvino",
        "import openvino",
        "class Scheduler",
        "LaboratoryManager",
        "ControlProxy(",
        "requests.post",
        "gh api",
    )
    for token in forbidden:
        assert token not in source
    for token in (
        'scheduler_modified: bool = False',
        'control_proxy_modified: bool = False',
        'github_mutation_performed: bool = False',
    ):
        assert token in source


def test_r12_does_not_claim_multi_laboratory_validation_for_one_lab() -> None:
    source = MODULE.read_text(encoding="utf-8")
    assert "distinct_laboratory_count: int = 1" in source
    assert "multi_laboratory_pipeline_eligible: bool = False" in source
    assert "multi_laboratory_aggregation_performed: bool = False" in source
    assert "multi-laboratory aggregation is deferred" in source


def test_r12_systematic_deliverables_are_present_and_consistent() -> None:
    for path in (REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
        text = path.read_text(encoding="utf-8")
        assert "0287-r7-r12" in text
    manifest = MANIFEST.read_text(encoding="utf-8")
    for path in (MODULE, REPORT, ARCH, DOT, CHANGELOG):
        assert str(path.relative_to(ROOT)) in manifest
    assert "INSTALLATION.md" in manifest
    assert "reviewed and unchanged" in manifest
