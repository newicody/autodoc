from pathlib import Path

from context.multi_laboratory_evidence_aggregation_reuse_audit_0287 import (
    audit_multi_laboratory_evidence_aggregation_reuse,
    load_audit_sources,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/multi_laboratory_evidence_provenance_contract_0287.py"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
REPORT = ROOT / "PHASE0287_R3_MULTI_LABORATORY_EVIDENCE_PROVENANCE_CONTRACT_REPORT.md"
ARCH = ROOT / "doc/architecture/MULTI_LABORATORY_EVIDENCE_PROVENANCE_CONTRACT_0287.md"
DOT = ROOT / "doc/architecture/MULTI_LABORATORY_EVIDENCE_PROVENANCE_CONTRACT_0287.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R3_MULTI_LABORATORY_EVIDENCE_PROVENANCE_CONTRACT.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R3_MULTI_LABORATORY_EVIDENCE_PROVENANCE_CONTRACT.md"


def test_r3_reuses_visit_and_transfer_contracts() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "LaboratoryVisitRequest" in text
    assert "LaboratoryVisitResult" in text
    assert "validate_laboratory_visit_result" in text
    assert "SpecialistTransferRequest" in text
    assert "validate_specialist_transfer_chain" in text


def test_r3_exposes_audit_markers() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "class MultiLaboratoryEvidenceProvenance",
        "laboratory_ref",
        "visit_ref",
        "specialist_ref",
        "source_ref",
    ):
        assert marker in text


def test_r3_has_no_backend_or_parallel_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "import subprocess", "import requests", "import urllib", "import httpx",
        "Scheduler(", "EventBus(", "LaboratoryManager", "QdrantClient",
    ):
        assert forbidden not in text
    for marker in (
        "deduplication_performed", "contradiction_detection_performed",
        "weighting_authorized", "durable_state_written",
        "scheduler_selection_allowed", "sql_remains_durable_authority",
        "scheduler_remains_only_orchestrator",
    ):
        assert marker in text


def test_actual_audit_progresses_cumulatively_after_r3() -> None:
    result = audit_multi_laboratory_evidence_aggregation_reuse(
        load_audit_sources(ROOT)
    )
    r4 = "0287-r4-multi-laboratory-evidence-digest-deduplication"
    assert (
        "0287-r3-multi-laboratory-evidence-provenance-contract"
        in result.completed_phases
    )
    if r4 in result.completed_phases:
        assert result.next_recommended_patch == (
            "0287-r5-multi-laboratory-evidence-contradiction-detection"
        )
    else:
        assert result.next_recommended_patch == r4


def test_installation_was_reviewed_without_change() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0286-r4`." in text
    assert "Ne pas utiliser `--delete`" in text
    report = REPORT.read_text(encoding="utf-8")
    assert "INSTALLATION.md reviewed" in report
    assert "No update required for 0287-r3" in report


def test_systematic_deliverables_exist() -> None:
    for path in (SOURCE, REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
