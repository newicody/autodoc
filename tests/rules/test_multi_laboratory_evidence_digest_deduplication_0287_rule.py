from pathlib import Path

from context.multi_laboratory_evidence_aggregation_reuse_audit_0287 import (
    audit_multi_laboratory_evidence_aggregation_reuse,
    load_audit_sources,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "src/context/"
    "multi_laboratory_evidence_digest_deduplication_0287.py"
)
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)
REPORT = (
    ROOT
    / "PHASE0287_R4_MULTI_LABORATORY_EVIDENCE_DIGEST_"
    "DEDUPLICATION_REPORT.md"
)
ARCH = (
    ROOT
    / "doc/architecture/"
    "MULTI_LABORATORY_EVIDENCE_DIGEST_DEDUPLICATION_0287.md"
)
DOT = (
    ROOT
    / "doc/architecture/"
    "MULTI_LABORATORY_EVIDENCE_DIGEST_DEDUPLICATION_0287.dot"
)
CHANGELOG = (
    ROOT
    / "doc/CHANGELOG_0287_R4_MULTI_LABORATORY_EVIDENCE_"
    "DIGEST_DEDUPLICATION.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0287_R4_MULTI_LABORATORY_"
    "EVIDENCE_DIGEST_DEDUPLICATION.md"
)


def test_r4_exposes_audit_markers() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "class MultiLaboratoryEvidenceDeduplicationResult",
        "duplicate_evidence_refs",
        "canonical_evidence_refs",
    ):
        assert marker in text


def test_r4_reuses_r2_and_r3_contracts() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "MultiLaboratoryEvidenceAggregate" in text
    assert "MultiLaboratoryEvidenceItem" in text
    assert "MultiLaboratoryEvidenceProvenance" in text
    assert "validate_multi_laboratory_evidence_provenance" in text


def test_r4_preserves_claim_variants_for_r5() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "retained_evidence_items" in text
    assert "claim_variant_evidence_refs" in text
    assert '"contradiction_detection_performed": False' in text


def test_r4_has_no_backend_or_parallel_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "import subprocess",
        "import requests",
        "import urllib",
        "import httpx",
        "Scheduler(",
        "EventBus(",
        "LaboratoryManager",
        "QdrantClient",
    ):
        assert forbidden not in text
    for marker in (
        "sql_remains_durable_authority",
        "scheduler_remains_only_orchestrator",
        "durable_state_written",
        "scheduler_selection_allowed",
    ):
        assert marker in text


def test_actual_audit_progresses_cumulatively_after_r4() -> None:
    result = audit_multi_laboratory_evidence_aggregation_reuse(
        load_audit_sources(ROOT)
    )
    phases = tuple(result.completed_phases)
    r5 = "0287-r5-multi-laboratory-evidence-contradiction-detection"
    r6 = "0287-r6-multi-laboratory-evidence-operator-weighting-policy"
    assert (
        "0287-r4-multi-laboratory-evidence-digest-deduplication"
        in phases
    )
    if r6 in phases:
        assert result.next_recommended_patch == (
            "0287-r7-multi-laboratory-evidence-durable-history"
        )
    elif r5 in phases:
        assert result.next_recommended_patch == r6
    else:
        assert result.next_recommended_patch == r5

def test_installation_was_reviewed_without_change() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0286-r4`." in text
    assert "Ne pas utiliser `--delete`" in text
    report = REPORT.read_text(encoding="utf-8")
    assert "INSTALLATION.md reviewed" in report
    assert "No update required for 0287-r4" in report


def test_systematic_deliverables_exist() -> None:
    for path in (SOURCE, REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
