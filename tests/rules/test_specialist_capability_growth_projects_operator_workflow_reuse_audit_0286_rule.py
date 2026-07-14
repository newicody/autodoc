from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_capability_growth_projects_operator_workflow_reuse_audit_0286.py"
TOOL = ROOT / "tools/run_specialist_capability_growth_projects_operator_workflow_reuse_audit_0286.py"
REPORT = ROOT / "PHASE0286_R1_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_REUSE_AUDIT_REPORT.md"
ARCH = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_REUSE_AUDIT_0286.md"
PLAN = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_DEVELOPMENT_PLAN_0286.md"
DOT = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_REUSE_AUDIT_0286.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0286_R1_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_REUSE_AUDIT.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0286_R1_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_REUSE_AUDIT.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
PROJECT_CONFIG = ROOT / "templates/github/projects-repository/projectv2_views.json"


def test_audit_is_source_only_and_has_no_runtime_or_remote_backend() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "import requests",
        "import urllib",
        "import subprocess",
        "import psycopg",
        "import qdrant",
        "import openvino",
        "Scheduler(",
        "EventBus(",
        "class LaboratoryManager",
    )
    for token in forbidden:
        assert token not in text
    assert "load_audit_sources" in text
    assert '"github_projects_authoritative": False' in text
    assert '"scheduler_remains_only_orchestrator": True' in text


def test_cli_has_no_execute_or_network_option() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert '"--root"' in text
    assert '"--format"' in text
    assert '"--execute"' not in text
    assert "requests" not in text
    assert "urllib" not in text
    assert "subprocess" not in text


def test_systematic_deliverables_and_remaining_plan_exist() -> None:
    for path in (SOURCE, TOOL, REPORT, ARCH, PLAN, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
    plan = PLAN.read_text(encoding="utf-8")
    for token in (
        "0286-r2",
        "0286-r3",
        "0286-r4",
        "0286-r5",
        "0286-r6",
        "0286-r7",
        "0286-r8",
        "0287",
        "0288",
        "0289",
        "Chalouf",
    ):
        assert token in plan


def test_architecture_reuses_existing_github_boundaries() -> None:
    text = ARCH.read_text(encoding="utf-8")
    for token in (
        "github_controlled_advisory_issue_publication_0281.py",
        "apply_github_project_v2_operator_authorized_mutations_0282.py",
        "GitHub Projects reste non autoritatif",
        "SQL reste l’autorité durable",
        "Scheduler reste l’unique autorité d’orchestration",
        "Qdrant reste projection/rappel",
    ):
        assert token in text


def test_projects_installation_was_reviewed_without_unnecessary_change() -> None:
    installation = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0284-r9`." in installation
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in installation
    assert "Ne pas utiliser `--delete`" in installation
    report = REPORT.read_text(encoding="utf-8")
    assert "INSTALLATION.md reviewed" in report
    assert "No update required for 0286-r1" in report


def test_existing_project_configuration_has_the_identified_gap() -> None:
    text = PROJECT_CONFIG.read_text(encoding="utf-8")
    assert '"Thème"' in text
    assert '"Affichage"' in text
    assert '"Copilot"' in text
    assert "Révision spécialiste" not in text
    assert "Décision capacité" not in text
