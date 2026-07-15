from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_capability_growth_projects_publication_plan_0286.py"
REPORT = ROOT / "PHASE0286_R5_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_0286.md"
GRAPH = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_0286.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0286_R5_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0286_R5_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_publication_plan_is_immutable_digest_bound_and_collision_guarded() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "@dataclass(frozen=True, slots=True)" in text
    assert "class SpecialistCapabilityGrowthProjectsPublicationPlan" in text
    assert "plan_digest" in text
    assert "comment_body_sha256" in text
    assert "projection_digest_sha256" in text
    assert "idempotency marker" in text
    assert "collision" in text


def test_publication_plan_reuses_r2_projection_and_r4_fields() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "SpecialistCapabilityGrowthProjectsReviewProjection" in text
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


def test_publication_plan_contains_no_remote_adapter_or_backend() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "import requests",
        "import httpx",
        "import urllib",
        "import subprocess",
        "gh api",
        "graphql mutation",
        "import psycopg",
        "import qdrant",
        "import openvino",
        "Scheduler(",
        "EventBus(",
        "LaboratoryManager",
    )

    for marker in forbidden:
        assert marker not in text


def test_plan_locks_authority_and_non_mutation_flags() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    for marker in (
        "remote_mutation_allowed",
        "github_mutation_performed",
        "issue_comment_published",
        "projectv2_mutation_performed",
        "github_projects_authoritative",
        "sql_remains_durable_authority",
        "scheduler_remains_only_orchestrator",
        "qdrant_authoritative",
    ):
        assert marker in text
    assert "default=False" in text


def test_systematic_deliverables_and_code_rule_review_exist() -> None:
    for path in (REPORT, ARCHITECTURE, GRAPH, CHANGELOG, MANIFEST):
        assert path.is_file(), path

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPORT, ARCHITECTURE, CHANGELOG, MANIFEST)
    )
    for marker in (
        "code_rule_review: done",
        "live_path_status: n/a",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: false",
        "0286-r6-specialist-capability-growth-projects-operator-authorized-adapter",
    ):
        assert marker in combined


def test_projects_installation_was_reviewed_without_unnecessary_change() -> None:
    installation = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0286-r4`." in installation
    assert "Version du guide : `0286-r3`." in installation
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in installation
    assert "Ne pas utiliser `--delete`" in installation

    report = REPORT.read_text(encoding="utf-8")
    assert "INSTALLATION.md reviewed" in report
    assert "No update required for 0286-r5" in report
