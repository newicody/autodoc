from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "templates/github/projects-repository"
CONFIG = BUNDLE / "projectv2_views.json"
RECONCILE = BUNDLE / "scripts/reconcile_projectv2_configuration.py"
PROJECT = BUNDLE / "scripts/project_copilot_advisory_fields.py"
WORKFLOW = BUNDLE / ".github/workflows/autodoc-controlled-research.yml"
INSTALLATION = BUNDLE / "INSTALLATION.md"


def test_project_management_remains_inside_the_copied_bundle() -> None:
    assert CONFIG.is_file()
    assert RECONCILE.is_file()
    assert PROJECT.is_file()
    assert not (ROOT / "src/context/projectv2_views.py").exists()
    assert not (ROOT / "tools/reconcile_projectv2_configuration.py").exists()


def test_workflow_remains_read_only_and_cannot_self_authorize_publication() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "issues: read" in text
    assert "issues: write" not in text
    assert "project_copilot_advisory_fields.py" not in text
    assert "publish_github_advisory_issue_comment_0281.py" not in text


def test_configuration_preserves_the_organized_views_and_authority_split() -> None:
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert value["schema"] == "autodoc.github.projects_repository_configuration.v1"
    assert value["project"] == {"owner_kind": "user", "owner": "newicody", "number": 3}
    names = {view["name"] for view in value["views"]}
    organized_view_names = {
        "Recherches",
        "Résultats",
        "Copilot",
        "Connaissances serveur",
        "Boîtes de thèmes",
        "Historique",
        "Tous",
    }
    assert organized_view_names.issubset(names)
    projection = value["copilot_projection"]
    assert "Résumé" not in projection.values()
    assert "Serveur" not in projection.values()


def test_mutation_adapters_require_operator_gates_and_reuse_0281() -> None:
    combined = RECONCILE.read_text(encoding="utf-8") + PROJECT.read_text(encoding="utf-8")
    for token in (
        "--execute",
        "--confirm-plan-digest",
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_PROJECT_CONFIGURATION_ALLOWED",
        "AUTODOC_PROJECT_PROJECTION_ALLOWED",
        "policy_decision_id must start with policy:",
        "operator_decision must be approve",
    ):
        assert token in combined
    installation = INSTALLATION.read_text(encoding="utf-8")
    assert "publish_github_advisory_issue_comment_0281.py" in installation
    assert "Le workflow ne publie pas lui-même son avis" in installation
