from pathlib import Path

from context.multi_laboratory_evidence_aggregation_reuse_audit_0287 import (
    audit_multi_laboratory_evidence_aggregation_reuse,
    load_audit_sources,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "src/context/"
    "multi_laboratory_evidence_contradiction_detection_0287.py"
)
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    "autodoc-controlled-research.yml"
)
REPORT = (
    ROOT
    / "PHASE0287_R5_MULTI_LABORATORY_EVIDENCE_"
    "CONTRADICTION_DETECTION_REPORT.md"
)
ARCH = (
    ROOT
    / "doc/architecture/"
    "MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_0287.md"
)
DOT = (
    ROOT
    / "doc/architecture/"
    "MULTI_LABORATORY_EVIDENCE_CONTRADICTION_DETECTION_0287.dot"
)
CHANGELOG = (
    ROOT
    / "doc/CHANGELOG_0287_R5_MULTI_LABORATORY_EVIDENCE_"
    "CONTRADICTION_DETECTION.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0287_R5_MULTI_LABORATORY_"
    "EVIDENCE_CONTRADICTION_DETECTION.md"
)


def test_r5_exposes_audit_markers() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "class MultiLaboratoryEvidenceContradiction",
        "contradiction_refs",
        "unresolved_contradictions",
    ):
        assert marker in text


def test_r5_consumes_r4_without_resolving_or_weighting() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "MultiLaboratoryEvidenceDeduplicationResult" in text
    assert "weighting_authorized" in text
    assert "resolution_state" in text
    assert '"unresolved"' in text
    assert "scheduler_selection_allowed" in text


def test_r5_has_no_backend_or_parallel_authority() -> None:
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
        "laboratory_self_authorization_allowed",
        "specialist_self_authorization_allowed",
    ):
        assert marker in text


def test_actual_audit_advances_to_r6() -> None:
    result = audit_multi_laboratory_evidence_aggregation_reuse(
        load_audit_sources(ROOT)
    )
    assert (
        "0287-r5-multi-laboratory-evidence-contradiction-detection"
        in result.completed_phases
    )
    assert result.next_recommended_patch == (
        "0287-r6-multi-laboratory-evidence-operator-weighting-policy"
    )


def test_installation_guide_is_now_shorter_and_token_focused() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version actuelle du guide : `0287-r5`." in text
    assert len(text.splitlines()) < 380
    for marker in (
        "gh auth refresh -h github.com -s project",
        'export GITHUB_TOKEN="$(gh auth token -h github.com)"',
        'export AUTODOC_PROJECT_TOKEN="$GITHUB_TOKEN"',
        "`AUTODOC_COPILOT_TOKEN`",
        "Ne pas utiliser `--delete`",
        "Version du guide : `0286-r4`.",
        "Version du guide : `0286-r3`.",
        "Version du guide : `0284-r9`.",
        "Version du guide : `0284-r1-r5`.",
    ):
        assert marker in text
    assert "non utilisé par le workflow actuel" in text


def test_workflow_really_uses_automatic_github_token() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "GITHUB_TOKEN: ${{ github.token }}" in text
    assert "copilot-requests: write" in text
    assert "AUTODOC_COPILOT_TOKEN" not in text


def test_systematic_deliverables_exist() -> None:
    for path in (SOURCE, REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
