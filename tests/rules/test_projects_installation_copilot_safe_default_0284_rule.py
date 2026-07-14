from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    / "autodoc-controlled-research.yml"
)
ADVISORY_SCRIPT = (
    ROOT / "templates/github/scripts/run_autodoc_copilot_advisory.py"
)
ARCHITECTURE = (
    ROOT / "doc/architecture/PROJECTS_COPILOT_SAFE_DEFAULT_0284.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    / "MANIFEST_0284_R1_R5_PROJECTS_INSTALLATION_COPILOT_SAFE_DEFAULT.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    / "CHANGELOG_0284_R1_R5_PROJECTS_INSTALLATION_COPILOT_SAFE_DEFAULT.md"
)
REPORT = (
    ROOT
    / "PHASE0284_R1_R5_PROJECTS_INSTALLATION_COPILOT_SAFE_DEFAULT_REPORT.md"
)


def test_installation_starts_with_copilot_disabled() -> None:
    source = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0284-r1-r5`." in source
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in source
    assert "Cette valeur est le défaut d'installation" in source
    assert "Après un premier dispatch validé sans Copilot" in source
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=true" in source
    assert source.index("AUTODOC_COPILOT_ADVISORY_ENABLED=false") < source.index(
        "AUTODOC_COPILOT_ADVISORY_ENABLED=true"
    )


def test_installation_and_workflow_use_ephemeral_authentication() -> None:
    installation = INSTALLATION.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "copilot-requests: write" in workflow
    assert "GITHUB_TOKEN: ${{ github.token }}" in workflow
    assert 'AUTODOC_COPILOT_REQUIRED: "false"' in workflow
    assert "secrets.AUTODOC_COPILOT_TOKEN" not in workflow
    assert "Ne pas créer de secret `AUTODOC_COPILOT_TOKEN`" in installation


def test_optional_advisory_failure_is_non_blocking() -> None:
    source = ADVISORY_SCRIPT.read_text(encoding="utf-8")
    assert "def _unavailable(" in source
    assert "return 1 if required else 0" in source
    assert 'required = _enabled("AUTODOC_COPILOT_REQUIRED")' in source
    assert "output_path.unlink(missing_ok=True)" in source


def test_phase_documents_lock_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ARCHITECTURE, MANIFEST, CHANGELOG, REPORT)
    )
    for required in (
        "initial_copilot_enabled: false",
        "advisory_required: false",
        "github_token_ephemeral: true",
        "durable_copilot_secret_required: false",
        "workflow_modified: false",
        "scheduler_modified: false",
        "external_dependencies_added: false",
    ):
        assert required in combined
