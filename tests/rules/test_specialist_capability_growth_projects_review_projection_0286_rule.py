from pathlib import Path

from context.specialist_capability_growth_projects_operator_workflow_reuse_audit_0286 import (
    audit_specialist_capability_growth_projects_operator_workflow_reuse,
    load_audit_sources,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_capability_growth_projects_review_projection_0286.py"
REPORT = ROOT / "PHASE0286_R2_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_0286.md"
GRAPH = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_0286.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0286_R2_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0286_R2_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_review_projection_contract_is_immutable_and_non_authoritative() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "@dataclass(frozen=True, slots=True)" in text
    assert "class SpecialistCapabilityGrowthProjectsReviewProjection" in text
    assert "github_projects_authoritative" in text
    assert "default=False" in text
    assert "publication_performed" in text
    assert "projectv2_mutation_performed" in text
    assert "issue_comment_published" in text


def test_review_projection_reuses_closed_0285_evidence_and_preserves_authorities() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    required = (
        "phase_0285_closed",
        "durable_sql_history_recorded",
        "scheduler_selection_performed",
        "laboratory_execution_performed",
        "eventbus_observation_published",
        "passive_supervisor_read_model_valid",
        "sql_remains_durable_authority",
        "scheduler_remains_only_orchestrator",
        "qdrant_authoritative",
        "copilot_authoritative",
    )
    for marker in required:
        assert marker in text


def test_review_projection_has_no_backend_or_remote_mutation_adapter() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "import requests",
        "import httpx",
        "from qdrant_client",
        "import qdrant_client",
        "import sqlalchemy",
        "subprocess.run",
        "gh api",
        "graphql mutation",
        "Scheduler(",
        "EventBus(",
        "LaboratoryManager",
    )

    for marker in forbidden:
        assert marker not in text


def test_review_projection_declares_the_planned_projectv2_review_fields() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    for field_name in (
        "Spécialiste",
        "Révision spécialiste",
        "Capacité proposée",
        "Action capacité",
        "Décision capacité",
        "Statut révision",
        "Référence SQL",
        "Digest décision",
        "Laboratoire",
    ):
        assert field_name in text


def test_phase_deliverables_exist_and_installation_review_is_documented() -> None:
    for path in (REPORT, ARCHITECTURE, GRAPH, CHANGELOG, MANIFEST):
        assert path.is_file(), path

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPORT, ARCHITECTURE, CHANGELOG, MANIFEST)
    )
    assert "INSTALLATION.md" in combined
    assert "No update" in combined or "no update" in combined

    installation = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0284-r9`." in installation
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in installation
    assert "Ne pas utiliser `--delete`" in installation


def test_reuse_audit_advances_from_r2_to_r3() -> None:
    result = audit_specialist_capability_growth_projects_operator_workflow_reuse(
        load_audit_sources(ROOT)
    )

    assert (
        "0286-r2-specialist-capability-growth-projects-review-projection-contract"
        in result.completed_phases
    )
    assert result.next_recommended_patch == (
        "0286-r3-specialist-capability-growth-projects-request-form-contract"
    )
