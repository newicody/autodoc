from pathlib import Path

from context.multi_laboratory_evidence_aggregation_reuse_audit_0287 import (
    audit_multi_laboratory_evidence_aggregation_reuse,
    load_audit_sources,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/multi_laboratory_evidence_durable_history_0287.py"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
REPORT = ROOT / "PHASE0287_R7_MULTI_LABORATORY_EVIDENCE_DURABLE_HISTORY_REPORT.md"
ARCH = ROOT / "doc/architecture/MULTI_LABORATORY_EVIDENCE_DURABLE_HISTORY_0287.md"
DOT = ROOT / "doc/architecture/MULTI_LABORATORY_EVIDENCE_DURABLE_HISTORY_0287.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_MULTI_LABORATORY_EVIDENCE_DURABLE_HISTORY.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_MULTI_LABORATORY_EVIDENCE_DURABLE_HISTORY.md"


def test_r7_exposes_audit_markers():
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "class MultiLaboratoryEvidenceHistoryEntry",
        "class MultiLaboratoryEvidenceHistoryPort",
        "sql_ref",
        "append",
    ):
        assert marker in text


def test_r7_requires_approved_r6_decision():
    text = SOURCE.read_text(encoding="utf-8")
    assert "MultiLaboratoryEvidenceWeightingDecision" in text
    assert "weighting_authorized" in text
    assert "durable_history_append_allowed" in text
    assert "operator-approved" in text


def test_r7_has_no_backend_or_parallel_authority():
    text = SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "import sqlite3",
        "import psycopg",
        "import sqlalchemy",
        "import subprocess",
        "Scheduler(",
        "EventBus(",
        "LaboratoryManager",
        "QdrantClient",
    ):
        assert forbidden not in text


def test_actual_audit_advances_to_r8():
    result = audit_multi_laboratory_evidence_aggregation_reuse(
        load_audit_sources(ROOT)
    )
    assert (
        "0287-r7-multi-laboratory-evidence-durable-history"
        in result.completed_phases
    )
    assert result.next_recommended_patch == (
        "0287-r8-multi-laboratory-evidence-"
        "scheduler-selection-constraints"
    )


def test_installation_was_reviewed_without_change():
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "newicody/projects" in text
    assert "Ne pas utiliser `--delete`" in text
    report = REPORT.read_text(encoding="utf-8")
    assert "INSTALLATION.md reviewed" in report
    assert "No update required for 0287-r7" in report


def test_systematic_deliverables_exist():
    for path in (SOURCE, REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
