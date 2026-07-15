from pathlib import Path

from context.specialist_capability_growth_projects_operator_workflow_reuse_audit_0286 import (
    audit_specialist_capability_growth_projects_operator_workflow_reuse,
    load_audit_sources,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "src/context/"
    "specialist_capability_growth_projects_closed_loop_smoke_0286.py"
)
TOOL = (
    ROOT
    / "tools/run_specialist_capability_growth_projects_"
    "closed_loop_smoke_0286.py"
)
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)
REPORT = (
    ROOT
    / "PHASE0286_R8_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_"
    "CLOSED_LOOP_SMOKE_REPORT.md"
)
ARCH = (
    ROOT
    / "doc/architecture/"
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_CLOSED_LOOP_SMOKE_0286.md"
)
DOT = (
    ROOT
    / "doc/architecture/"
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_CLOSED_LOOP_SMOKE_0286.dot"
)
CHANGELOG = (
    ROOT
    / "doc/CHANGELOG_0286_R8_SPECIALIST_CAPABILITY_GROWTH_"
    "PROJECTS_CLOSED_LOOP_SMOKE.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0286_R8_SPECIALIST_CAPABILITY_"
    "GROWTH_PROJECTS_CLOSED_LOOP_SMOKE.md"
)


def test_r8_exposes_the_audit_markers() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "SpecialistCapabilityGrowthProjectsClosedLoopSmokeResult" in text
    assert "phase_0286_closed" in text


def test_r8_is_pure_and_creates_no_parallel_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "import subprocess",
        "import requests",
        "import urllib",
        "import httpx",
        "gh api",
        "Scheduler(",
        "EventBus(",
        "LaboratoryManager",
    ):
        assert forbidden not in text
    for marker in (
        "sql_remains_durable_authority",
        "scheduler_remains_only_orchestrator",
        "github_projects_authoritative",
        "new_scheduler_created",
        "new_global_specialist_registry_created",
    ):
        assert marker in text


def test_r8_separates_local_and_live_closure() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "local_contract_closed" in text
    assert "deployment_closed" in text
    assert "live_query_only" in text
    assert "require_live_readback" in text


def test_actual_audit_closes_0286() -> None:
    result = (
        audit_specialist_capability_growth_projects_operator_workflow_reuse(
            load_audit_sources(ROOT)
        )
    )
    assert (
        "0286-r8-specialist-capability-growth-projects-closed-loop-smoke"
        in result.completed_phases
    )
    assert result.next_recommended_patch == "0286-complete"


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
    assert "No update required for 0286-r8" in report
