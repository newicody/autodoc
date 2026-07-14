from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


ACTIVE_PROJECT_SURFACES = (
    ".github/workflows/autodoc-controlled-research.yml",
    ".github/ISSUE_TEMPLATE/research.yml",
    ".github/ISSUE_TEMPLATE/theme.yml",
    ".github/ISSUE_TEMPLATE/transversal-event.yml",
)

BUNDLE_REQUIRED_SURFACES = (
    "templates/github/projects-repository/README.md",
    "templates/github/projects-repository/.github/workflows/autodoc-controlled-research.yml",
)

INVALID_AUTODOC_PROJECT_MODE_SURFACES = (
    "src/context/github_project_v2_visibility_projection_0284.py",
    "tools/run_github_project_v2_visibility_0284.py",
)


def test_autodoc_has_no_active_projects_management_surfaces() -> None:
    for relative_path in ACTIVE_PROJECT_SURFACES:
        assert not (ROOT / relative_path).exists(), relative_path


def test_projects_repository_bundle_remains_the_copy_source() -> None:
    for relative_path in BUNDLE_REQUIRED_SURFACES:
        assert (ROOT / relative_path).is_file(), relative_path

    readme = (ROOT / BUNDLE_REQUIRED_SURFACES[0]).read_text(encoding="utf-8")
    assert "newicody/projects" in readme
    assert "copié" in readme


def test_project_view_management_is_not_an_autodoc_runtime_mode() -> None:
    for relative_path in INVALID_AUTODOC_PROJECT_MODE_SURFACES:
        assert not (ROOT / relative_path).exists(), relative_path


def test_documentation_declares_external_connector_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    operator_doc = (
        ROOT / "doc/operator/GITHUB_PROJECT_ACTIONS_CONFIGURATION_0272.md"
    ).read_text(encoding="utf-8")

    assert "Autodoc has no project-management mode" in readme
    assert "Autodoc/MissiPy ne possède pas de mode de gestion de projet" in operator_doc
    assert "templates/github/projects-repository/" in operator_doc
    assert "Mode ProjectV2 natif" not in operator_doc
