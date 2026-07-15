from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    "build_copilot_advisory_publication_preview.py"
)
RUNNER = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    "project_copilot_advisory_from_run.py"
)
RUNBOOK = (
    ROOT
    / "templates/github/projects-repository/"
    "COPILOT_ADVISORY_PUBLICATION.md"
)
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    "autodoc-controlled-research.yml"
)
REPORT = (
    ROOT
    / "PHASE0287_R7_R1_COPILOT_ADVISORY_PROJECTV2_"
    "PUBLICATION_REPORT.md"
)


def test_artifact_correlation_is_required():
    text = BUILDER.read_text(encoding="utf-8")
    for marker in (
        "request/advisory correlation mismatch",
        "request/manifest correlation mismatch",
        "authoritative request digest mismatch",
        "Copilot advisory digest mismatch",
        "advisory_is_authority",
        "operator_decision_required",
        "publication_gate_required",
    ):
        assert marker in text


def test_runner_reuses_controlled_projection_adapter():
    text = RUNNER.read_text(encoding="utf-8")
    assert "project_copilot_advisory_fields" in text
    assert "CopilotFieldProjectionCommand" in text
    assert "execute_copilot_field_projection" in text
    assert "AUTODOC_REMOTE_MUTATION_ALLOWED" in text
    assert "AUTODOC_PROJECT_PROJECTION_ALLOWED" in text
    assert "--confirm-plan-digest" in text
    assert "workflow_self_authorized" in text


def test_workflow_still_cannot_self_publish():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Upload optional Copilot advisory" in text
    assert "project_copilot_advisory_from_run.py" not in text
    assert "project_copilot_advisory_fields.py" not in text


def test_installation_links_short_runbook_within_budget():
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "COPILOT_ADVISORY_PUBLICATION.md" in text
    assert len(text.splitlines()) < 380
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert "project_copilot_advisory_from_run.py" in runbook
    assert "AUTODOC_PROJECT_TOKEN" in runbook
    assert "plan_digest" in runbook


def test_report_explains_missing_visible_advisories():
    text = REPORT.read_text(encoding="utf-8")
    assert "artifact upload was already working" in text
    assert "field projection was not invoked" in text
