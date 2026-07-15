from pathlib import Path

from context.specialist_capability_growth_projects_operator_workflow_reuse_audit_0286 import (
    audit_specialist_capability_growth_projects_operator_workflow_reuse,
    load_audit_sources,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "src/context/"
    "specialist_capability_growth_projects_readback_readiness_0286.py"
)
TOOL = (
    ROOT
    / "tools/check_specialist_capability_growth_projects_readback_0286.py"
)
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)
REPORT = (
    ROOT
    / "PHASE0286_R7_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_"
    "READBACK_READINESS_REPORT.md"
)
ARCH = (
    ROOT
    / "doc/architecture/"
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_READINESS_0286.md"
)
DOT = (
    ROOT
    / "doc/architecture/"
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_READINESS_0286.dot"
)
CHANGELOG = (
    ROOT
    / "doc/CHANGELOG_0286_R7_SPECIALIST_CAPABILITY_GROWTH_"
    "PROJECTS_READBACK_READINESS.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0286_R7_SPECIALIST_CAPABILITY_"
    "GROWTH_PROJECTS_READBACK_READINESS.md"
)


def test_r7_exposes_the_audit_markers() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "SpecialistCapabilityGrowthProjectsReadbackEvidence" in text
    assert "remote_mutation_allowed" in text


def test_r7_contract_has_no_network_or_mutation_backend() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "import subprocess",
        "import requests",
        "import urllib",
        "import httpx",
        "gh api",
        "Scheduler(",
        "EventBus(",
        "class LaboratoryManager",
    ):
        assert forbidden not in text


def test_r7_tool_has_only_read_operations() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert '"--execute"' in text
    assert '"GET"' in text
    assert "query($itemId: ID!)" in text
    assert "updateProjectV2ItemFieldValue" not in text
    assert "createProjectV2" not in text


def test_actual_audit_advances_to_r8() -> None:
    result = (
        audit_specialist_capability_growth_projects_operator_workflow_reuse(
            load_audit_sources(ROOT)
        )
    )
    assert (
        "0286-r7-specialist-capability-growth-projects-readback-readiness"
        in result.completed_phases
    )
    assert result.next_recommended_patch == (
        "0286-r8-specialist-capability-growth-projects-closed-loop-smoke"
    )


def test_systematic_deliverables_exist() -> None:
    for path in (
        SOURCE,
        TOOL,
        REPORT,
        ARCH,
        DOT,
        CHANGELOG,
        MANIFEST,
    ):
        assert path.is_file(), path


def test_projects_installation_was_reviewed_without_unnecessary_change() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0286-r4`." in text
    assert "Ne pas utiliser `--delete`" in text
    report = REPORT.read_text(encoding="utf-8")
    assert "INSTALLATION.md reviewed" in report
    assert "No update required for 0286-r7" in report
