from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORM = (
    ROOT
    / "templates/github/projects-repository/.github/ISSUE_TEMPLATE/"
    / "specialist-capability-growth.yml"
)
SOURCE = ROOT / "src/context/github_specialist_capability_growth_issue_contract_0286.py"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
README = ROOT / "templates/github/projects-repository/README.md"
REPORT = ROOT / "PHASE0286_R3_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REQUEST_FORM_CONTRACT_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REQUEST_FORM_CONTRACT_0286.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0286_R3_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REQUEST_FORM_CONTRACT.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0286_R3_SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REQUEST_FORM_CONTRACT.md"


def test_dedicated_issue_form_expresses_request_without_approval() -> None:
    text = FORM.read_text(encoding="utf-8")
    for marker in (
        "specialist_ref",
        "base_specialist_version",
        "capability",
        "evidence_expectation",
        "requested_input_contract_refs",
        "requested_output_contract_refs",
        "requested_laboratory_capability_refs",
        "operator decision remains local",
        "La décision opérateur reste locale",
    ):
        assert marker in text
    assert "id: operator_approval" not in text
    assert "id: approve" not in text
    assert "Approuver la révision" not in text


def test_local_intake_is_immutable_stdlib_only_and_non_authoritative() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "GitHubSpecialistCapabilityGrowthIssueRequest",
        "dataclass(frozen=True, slots=True)",
        '"approval_authoritative": False',
        '"revision_authorized": False',
        '"scheduler_dispatch_allowed": False',
        '"operator_decision_remains_local": True',
    ):
        assert marker in text
    for forbidden in (
        "import requests",
        "from requests",
        "import qdrant_client",
        "from qdrant_client",
        "import openvino",
        "from openvino",
        "subprocess",
        "gh api",
        "Scheduler(",
        "LaboratoryManager",
    ):
        assert forbidden not in text


def test_projects_bundle_and_installation_are_updated_cumulatively() -> None:
    installation = INSTALLATION.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    assert "Version du guide : `0286-r3`." in installation
    assert "specialist-capability-growth.yml" in installation
    assert "specialist-capability-growth.yml" in readme
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in installation
    assert "Ne pas utiliser `--delete`" in installation
    assert "Version du guide : `0284-r9`." in installation
    assert "Version du guide : `0284-r1-r5`." in installation
    assert "0286-r3" in installation


def test_phase_documents_lock_runtime_and_installation_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPORT, ARCHITECTURE, MANIFEST, CHANGELOG)
    )
    for marker in (
        "projects_bundle_modified: true",
        "projects_installation_modified: true",
        "workflow_modified: false",
        "scheduler_modified: false",
        "sql_modified: false",
        "qdrant_modified: false",
        "external_dependencies_added: false",
        "operator decision remains local",
        "0286-r4-specialist-capability-growth-projectv2-fields-views",
    ):
        assert marker in combined
