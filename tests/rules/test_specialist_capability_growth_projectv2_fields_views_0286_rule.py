from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "templates/github/projects-repository/projectv2_views.json"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
REPORT = ROOT / "PHASE0286_R4_SPECIALIST_CAPABILITY_GROWTH_PROJECTV2_FIELDS_VIEWS_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTV2_FIELDS_VIEWS_0286.md"
GRAPH = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTV2_FIELDS_VIEWS_0286.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0286_R4_SPECIALIST_CAPABILITY_GROWTH_PROJECTV2_FIELDS_VIEWS.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0286_R4_SPECIALIST_CAPABILITY_GROWTH_PROJECTV2_FIELDS_VIEWS.md"


def test_projectv2_configuration_keeps_one_schema_and_user_project_identity() -> None:
    configuration = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert configuration["schema"] == (
        "autodoc.github.projects_repository_configuration.v1"
    )
    assert configuration["project"] == {
        "owner_kind": "user",
        "owner": "newicody",
        "number": 3,
    }


def test_review_surface_contains_no_authority_or_execution_claim() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    forbidden = (
        "github_projects_authoritative",
        "sql_write_allowed",
        "scheduler_dispatch_allowed",
        "laboratory_execution_allowed",
        "AUTODOC_REMOTE_MUTATION_ALLOWED=true",
        "gh api",
    )
    for marker in forbidden:
        assert marker not in text


def test_installation_is_cumulative_and_preview_first() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0286-r4`." in text
    assert "Version du guide : `0286-r3`." in text
    assert "Version du guide : `0284-r9`." in text
    assert "Version du guide : `0284-r1-r5`." in text
    assert "Révisions spécialistes" in text
    assert "--confirm-plan-digest '<PLAN_DIGEST>'" in text
    assert "Ne pas utiliser `--delete`" in text
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in text


def test_phase_deliverables_exist_and_lock_existing_boundaries() -> None:
    for path in (REPORT, ARCHITECTURE, GRAPH, CHANGELOG, MANIFEST):
        assert path.is_file(), path
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPORT, ARCHITECTURE, CHANGELOG, MANIFEST)
    )
    for marker in (
        "Scheduler",
        "SQL",
        "Qdrant",
        "GitHub Projects",
        "INSTALLATION.md",
        "0286-r5-specialist-capability-growth-projects-publication-plan",
    ):
        assert marker in combined
    assert "new Scheduler" not in combined
    assert "LaboratoryManager" not in combined
