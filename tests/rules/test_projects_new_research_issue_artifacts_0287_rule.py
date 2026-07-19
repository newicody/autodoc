from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    "autodoc-controlled-research.yml"
)
RESEARCH_FORM = (
    ROOT
    / "templates/github/projects-repository/.github/ISSUE_TEMPLATE/research.yml"
)
README = ROOT / "templates/github/projects-repository/README.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_only_new_projects_research_issues_trigger_automatically() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    research_form = RESEARCH_FORM.read_text(encoding="utf-8")

    for marker in (
        "issues:\n    types:\n      - opened",
        "github.repository == 'newicody/projects'",
        "github.event_name == 'issues'",
        "github.event.action == 'opened'",
        "startsWith(github.event.issue.title, '[Recherche] ')",
        "contains(github.event.issue.body, '### Question ou objectif')",
        "contains(github.event.issue.body, '### Résultat attendu')",
        'title: "[Recherche] "',
        "Un avis Copilot séparé est produit automatiquement",
    ):
        assert marker in workflow or marker in research_form

    assert "pull_request" not in workflow


def test_issue_event_resolves_initial_research_inputs() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for marker in (
        "AUTODOC_ISSUE_NUMBER:",
        "github.event.issue.number",
        'AUTODOC_REQUESTED_STATUS_RESOLVED: "Recherche"',
        'AUTODOC_REQUEST_MODE_RESOLVED: "initial"',
        'AUTODOC_PARENT_EVENT_REF_RESOLVED: ""',
        "ISSUE_NUMBER: ${{ env.AUTODOC_ISSUE_NUMBER }}",
        "AUTODOC_REQUESTED_STATUS: ${{ env.AUTODOC_REQUESTED_STATUS_RESOLVED }}",
        "AUTODOC_REQUEST_MODE: ${{ env.AUTODOC_REQUEST_MODE_RESOLVED }}",
    ):
        assert marker in workflow

    assert workflow.count(
        "ISSUE_NUMBER: ${{ env.AUTODOC_ISSUE_NUMBER }}"
    ) == 4


def test_automatic_research_run_requires_three_correlated_artifacts() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for marker in (
        'AUTODOC_COPILOT_REQUIRED_RESOLVED: "true"',
        "AUTODOC_COPILOT_REQUIRED: ${{ env.AUTODOC_COPILOT_REQUIRED_RESOLVED }}",
        "- name: Upload authoritative request",
        "- name: Upload optional Copilot advisory",
        "- name: Upload manifest",
        "steps.artifact-identity.outputs.request_name",
        "steps.artifact-identity.outputs.advisory_name",
        "steps.artifact-identity.outputs.manifest_name",
        "out/dual_artifact_manifest.json",
        "out/artifact_identity.json",
    ):
        assert marker in workflow

    # r16-r22 centralizes the automatic Issue route in the job gate.
    # Step-level repetitions are no longer required or desirable.
    assert workflow.count("github.event_name == 'issues'") == 1
    assert "github.event_name == 'workflow_dispatch'" not in workflow
    assert "inputs." not in workflow


def test_artifact_identity_separates_issues_and_runs() -> None:
    import sys

    src = ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from context.human_readable_artifact_identity_0287 import (
        build_human_readable_artifact_identity_bundle,
    )

    def bundle(issue_number: int, run_id: str):
        request_ref = f"github-request:newicody/projects:{issue_number}:request"
        advisory_ref = f"github-advisory:{issue_number}:advisory"
        manifest_ref = f"github-manifest:{issue_number}:manifest"
        return build_human_readable_artifact_identity_bundle(
            repository="newicody/projects",
            workflow_run_id=run_id,
            issue={
                "number": issue_number,
                "title": "[Recherche] Même titre",
            },
            request={
                "repository": "newicody/projects",
                "issue_number": issue_number,
                "title": "[Recherche] Même titre",
                "artifact_ref": request_ref,
            },
            advisory={
                "artifact_ref": advisory_ref,
                "request_artifact_ref": request_ref,
            },
            manifest={
                "manifest_ref": manifest_ref,
                "request_artifact_ref": request_ref,
                "advisory_artifact_ref": advisory_ref,
            },
        )

    issue_41_run_100 = bundle(41, "100")
    issue_42_run_100 = bundle(42, "100")
    issue_41_run_101 = bundle(41, "101")

    names_41 = {item.actions_name for item in issue_41_run_100.identities}
    names_42 = {item.actions_name for item in issue_42_run_100.identities}

    assert names_41.isdisjoint(names_42)
    assert issue_41_run_100.bundle_digest != issue_42_run_100.bundle_digest
    assert issue_41_run_100.bundle_digest != issue_41_run_101.bundle_digest
    assert issue_41_run_100.workflow_run_id == "100"
    assert issue_41_run_101.workflow_run_id == "101"


def test_installation_documents_projects_repository_and_view_boundary() -> None:
    text = README.read_text(encoding="utf-8") + INSTALLATION.read_text(
        encoding="utf-8"
    )

    for marker in (
        "newicody/projects",
        "issues.opened",
        "[Recherche]",
        "trois artefacts Actions distincts par Issue et par run",
        "Les vues ProjectV2 préparées restent la surface de classement",
        "AUTODOC_ISSUE_COMMENT_TOKEN",
        "--event issues",
    ):
        assert marker in text
