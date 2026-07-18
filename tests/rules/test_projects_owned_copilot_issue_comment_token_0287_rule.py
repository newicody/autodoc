from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    "autodoc-controlled-research.yml"
)


def test_projects_owns_bounded_advisory_comment_publication() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "issues: read" in text
    assert "issues: write" not in text
    assert "secrets.AUTODOC_ISSUE_COMMENT_TOKEN" in text
    assert "Build Projects-owned Copilot advisory preview" in text
    assert "Plan Projects-owned Copilot advisory comment" in text
    assert "Publish Projects-owned Copilot advisory comment" in text
    assert "build_copilot_advisory_v2_publication_preview.py" in text
    assert "publish_github_copilot_advisory_v2_issue_comment_0287.py" in text
    assert 'AUTODOC_REMOTE_MUTATION_ALLOWED: "true"' in text
    assert 'AUTODOC_ISSUE_PUBLICATION_ALLOWED: "true"' in text
    assert "project_copilot_advisory_fields.py" not in text
    assert "AUTODOC_PROJECT_TOKEN" not in text


def test_artifacts_are_uploaded_before_projects_comment_publication() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    upload_request = text.index("- name: Upload authoritative request")
    upload_advisory = text.index("- name: Upload optional Copilot advisory")
    upload_manifest = text.index("- name: Upload manifest")
    publish_comment = text.index(
        "- name: Publish Projects-owned Copilot advisory comment"
    )

    assert upload_request < publish_comment
    assert upload_advisory < publish_comment
    assert upload_manifest < publish_comment


def test_comment_publication_is_idempotent_and_read_back() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    for marker in (
        "--confirm-plan-digest",
        "copilot_issue_comment_plan_digest.txt",
        ".readback_verified == true",
        '.mutation_action == "created"',
        '.mutation_action == "replay-noop"',
    ):
        assert marker in text
