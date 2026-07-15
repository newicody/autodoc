from pathlib import Path

from context.multi_laboratory_evidence_aggregation_reuse_audit_0287 import (
    audit_multi_laboratory_evidence_aggregation_reuse,
    load_audit_sources,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "src/context/"
    "multi_laboratory_evidence_aggregation_reuse_audit_0287.py"
)
TOOL = (
    ROOT / "tools/audit_multi_laboratory_evidence_aggregation_reuse_0287.py"
)
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)
REPORT = (
    ROOT
    / "PHASE0287_R1_MULTI_LABORATORY_EVIDENCE_AGGREGATION_"
    "REUSE_AUDIT_REPORT.md"
)
ARCH = (
    ROOT
    / "doc/architecture/"
    "MULTI_LABORATORY_EVIDENCE_AGGREGATION_REUSE_AUDIT_0287.md"
)
DOT = (
    ROOT
    / "doc/architecture/"
    "MULTI_LABORATORY_EVIDENCE_AGGREGATION_REUSE_AUDIT_0287.dot"
)
ROADMAP = (
    ROOT
    / "doc/architecture/"
    "MULTI_LABORATORY_EVIDENCE_AGGREGATION_ROADMAP_0287.md"
)
CHANGELOG = (
    ROOT
    / "doc/CHANGELOG_0287_R1_MULTI_LABORATORY_EVIDENCE_"
    "AGGREGATION_REUSE_AUDIT.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0287_R1_MULTI_LABORATORY_"
    "EVIDENCE_AGGREGATION_REUSE_AUDIT.md"
)


def test_actual_repository_reuse_audit_is_green_and_recommends_r2() -> None:
    result = audit_multi_laboratory_evidence_aggregation_reuse(
        load_audit_sources(ROOT)
    )
    assert result.valid is True
    assert result.next_recommended_patch == (
        "0287-r2-multi-laboratory-evidence-aggregation-contract"
    )


def test_audit_is_source_only() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "import subprocess",
        "import requests",
        "import urllib",
        "import httpx",
        "Scheduler(",
        "EventBus(",
        "LaboratoryManager",
    ):
        assert forbidden not in text


def test_roadmap_locks_reuse_first_and_authority_split() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    for token in (
        "Scheduler remains the only orchestrator",
        "SQL remains the durable authority",
        "Qdrant remains projection and recall",
        "EventBus remains observation-only",
        "no LaboratoryManager",
        "no global evidence registry",
    ):
        assert token in text


def test_installation_guide_was_reviewed_without_change() -> None:
    installation = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0286-r4`." in installation
    assert "Ne pas utiliser `--delete`" in installation
    report = REPORT.read_text(encoding="utf-8")
    assert "INSTALLATION.md reviewed" in report
    assert "No update required for 0287-r1" in report


def test_systematic_deliverables_exist() -> None:
    for path in (
        SOURCE,
        TOOL,
        REPORT,
        ARCH,
        DOT,
        ROADMAP,
        CHANGELOG,
        MANIFEST,
    ):
        assert path.is_file(), path
