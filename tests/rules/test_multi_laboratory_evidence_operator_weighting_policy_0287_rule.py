from pathlib import Path

from context.multi_laboratory_evidence_aggregation_reuse_audit_0287 import (
    audit_multi_laboratory_evidence_aggregation_reuse,
    load_audit_sources,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "src/context/"
    "multi_laboratory_evidence_operator_weighting_policy_0287.py"
)
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)
REPORT = (
    ROOT
    / "PHASE0287_R6_MULTI_LABORATORY_EVIDENCE_OPERATOR_"
    "WEIGHTING_POLICY_REPORT.md"
)
ARCH = (
    ROOT
    / "doc/architecture/"
    "MULTI_LABORATORY_EVIDENCE_OPERATOR_WEIGHTING_POLICY_0287.md"
)
DOT = (
    ROOT
    / "doc/architecture/"
    "MULTI_LABORATORY_EVIDENCE_OPERATOR_WEIGHTING_POLICY_0287.dot"
)
CHANGELOG = (
    ROOT
    / "doc/CHANGELOG_0287_R6_MULTI_LABORATORY_EVIDENCE_"
    "OPERATOR_WEIGHTING_POLICY.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0287_R6_MULTI_LABORATORY_"
    "EVIDENCE_OPERATOR_WEIGHTING_POLICY.md"
)


def test_r6_exposes_audit_markers() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "class MultiLaboratoryEvidenceWeightingDecision",
        "operator_ref",
        "approve",
        "weighting_digest",
    ):
        assert marker in text


def test_r6_reuses_r5_and_explicit_operator_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "MultiLaboratoryEvidenceContradictionDetectionResult" in text
    assert "MultiLaboratoryEvidenceContradiction" in text
    assert "explicit_operator_authority" in text
    assert "durable_history_append_allowed" in text
    assert "unresolved_contradiction_refs" in text


def test_r6_has_no_backend_or_parallel_authority() -> None:
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
        "durable_state_written",
        "scheduler_selection_allowed",
        "scheduler_remains_only_orchestrator",
        "sql_remains_durable_authority",
        "laboratory_self_authorization_allowed",
        "specialist_self_authorization_allowed",
    ):
        assert marker in text


def test_actual_audit_progresses_cumulatively_after_r6() -> None:
    result = audit_multi_laboratory_evidence_aggregation_reuse(
        load_audit_sources(ROOT)
    )
    r7 = "0287-r7-multi-laboratory-evidence-durable-history"
    assert (
        "0287-r6-multi-laboratory-evidence-operator-weighting-policy"
        in result.completed_phases
    )
    if r7 in result.completed_phases:
        assert result.next_recommended_patch == (
            "0287-r8-multi-laboratory-evidence-"
            "scheduler-selection-constraints"
        )
    else:
        assert result.next_recommended_patch == r7
    assert result.weighting_policy_missing is False

def test_installation_was_reviewed_without_change() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "newicody/projects" in text
    assert "Ne pas utiliser `--delete`" in text
    report = REPORT.read_text(encoding="utf-8")
    assert "INSTALLATION.md reviewed" in report
    assert "No update required for 0287-r6" in report


def test_systematic_deliverables_exist() -> None:
    for path in (SOURCE, REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
