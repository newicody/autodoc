from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    "autodoc-controlled-research.yml"
)
SCRIPT = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    "run_workflow_dispatch_authoritative_request.py"
)
REPORT = (
    ROOT
    / "PHASE0281_R4_R1_WORKFLOW_DISPATCH_ISSUE_ENVELOPE_REPAIR_REPORT.md"
)


def test_workflow_uses_repair_adapter_and_explicit_paths() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Normalize event and build authoritative request" in workflow
    assert "AUTODOC_ISSUE_JSON:" in workflow
    assert "AUTODOC_EVENT_PATH:" in workflow
    assert "AUTODOC_NORMALIZED_EVENT_OUTPUT:" in workflow
    assert "run_workflow_dispatch_authoritative_request.py" in workflow


def test_adapter_reuses_authoritative_builder_and_keeps_authority() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    for required in (
        "build_autodoc_authoritative_request.py",
        "missipy.github.workflow_dispatch_issue_event.v1",
        "authoritative request Issue mismatch",
        'environment.pop("GITHUB_EVENT_PATH", None)',
    ):
        assert required in text
    for forbidden in (
        "gh api",
        "requests.",
        "urlopen(",
        "remote_mutation_requested=True",
    ):
        assert forbidden not in text


def test_projects_change_is_declared() -> None:
    report = REPORT.read_text(encoding="utf-8")
    assert "projects_repository_change_required: true" in report
    assert "newicody/projects" in report

def test_repair_preserves_current_cached_runtime_shape() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'AUTODOC_COPILOT_CLI_VERSION: "1.0.70"' in workflow
    assert "uses: actions/cache@v4" in workflow
    assert "uses: actions/upload-artifact@v7" in workflow
    assert "repository: newicody/autodoc" in workflow

