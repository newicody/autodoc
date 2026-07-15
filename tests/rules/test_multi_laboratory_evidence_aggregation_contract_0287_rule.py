from pathlib import Path

from context.multi_laboratory_evidence_aggregation_reuse_audit_0287 import (
    audit_multi_laboratory_evidence_aggregation_reuse,
    load_audit_sources,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "src/context/multi_laboratory_evidence_aggregation_contract_0287.py"
)
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
REPORT = (
    ROOT
    / "PHASE0287_R2_MULTI_LABORATORY_EVIDENCE_AGGREGATION_CONTRACT_REPORT.md"
)
ARCH = (
    ROOT
    / "doc/architecture/MULTI_LABORATORY_EVIDENCE_AGGREGATION_CONTRACT_0287.md"
)
DOT = (
    ROOT
    / "doc/architecture/MULTI_LABORATORY_EVIDENCE_AGGREGATION_CONTRACT_0287.dot"
)
CHANGELOG = (
    ROOT
    / "doc/CHANGELOG_0287_R2_MULTI_LABORATORY_EVIDENCE_AGGREGATION_CONTRACT.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0287_R2_MULTI_LABORATORY_EVIDENCE_AGGREGATION_CONTRACT.md"
)


def test_r2_reuses_the_existing_digest_bound_evidence_contract() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "from context.specialist_capability_growth_proposal_contract_0285" in text
    assert "SpecialistCapabilityEvidenceRef" in text
    assert "multi_laboratory_evidence_item_from_specialist_capability_evidence_ref" in text


def test_r2_exposes_the_audit_markers() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "class MultiLaboratoryEvidenceItem" in text
    assert "class MultiLaboratoryEvidenceAggregate" in text
    assert "aggregation_digest" in text


def test_r2_has_no_backend_or_parallel_authority() -> None:
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
        "scheduler_selection_allowed",
        "laboratory_self_authorization_allowed",
        "specialist_self_authorization_allowed",
        "qdrant_authoritative",
        "github_projects_authoritative",
    ):
        assert marker in text


def test_actual_audit_progresses_cumulatively_after_r2() -> None:
    result = audit_multi_laboratory_evidence_aggregation_reuse(
        load_audit_sources(ROOT)
    )
    phases = tuple(result.completed_phases)
    r3 = "0287-r3-multi-laboratory-evidence-provenance-contract"
    r4 = "0287-r4-multi-laboratory-evidence-digest-deduplication"
    r5 = "0287-r5-multi-laboratory-evidence-contradiction-detection"
    r6 = "0287-r6-multi-laboratory-evidence-operator-weighting-policy"
    assert (
        "0287-r2-multi-laboratory-evidence-aggregation-contract"
        in phases
    )
    if r6 in phases:
        assert result.next_recommended_patch == (
            "0287-r7-multi-laboratory-evidence-durable-history"
        )
    elif r5 in phases:
        assert result.next_recommended_patch == r6
    elif r4 in phases:
        assert result.next_recommended_patch == r5
    elif r3 in phases:
        assert result.next_recommended_patch == r4
    else:
        assert result.next_recommended_patch == r3

def test_installation_was_reviewed_without_change() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0286-r4`." in text
    assert "Ne pas utiliser `--delete`" in text
    report = REPORT.read_text(encoding="utf-8")
    assert "INSTALLATION.md reviewed" in report
    assert "No update required for 0287-r2" in report


def test_systematic_deliverables_exist() -> None:
    for path in (SOURCE, REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
