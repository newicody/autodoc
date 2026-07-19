from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = (
    ROOT / "templates/github/autodoc-dual-artifact.yml",
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    "autodoc-controlled-research.yml",
)


def test_workflows_use_scoped_copilot_token_and_separate_uploads() -> None:
    for path in WORKFLOWS:
        text = path.read_text(encoding="utf-8")
        for marker in (
            "contents: read",
            "issues: read",
            "copilot-requests: write",
            "GITHUB_TOKEN: ${{ github.token }}",
            "autodoc-authoritative-request",
            "autodoc-copilot-advisory",
            "autodoc-dual-artifact-manifest",
        ):
            assert marker in text
        for forbidden in (
            "contents: write",
            "issues: write",
            "pull_request_target",
            "secrets.AUTODOC_COPILOT_TOKEN",
        ):
            assert forbidden not in text

    generic = WORKFLOWS[0].read_text(encoding="utf-8")
    assert 'AUTODOC_COPILOT_REQUIRED: "false"' in generic
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED" in generic

    automatic = WORKFLOWS[1].read_text(encoding="utf-8")
    assert 'AUTODOC_COPILOT_REQUIRED_RESOLVED: "true"' in automatic
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED" not in automatic


def test_controlled_research_builds_the_issue_event_before_the_request() -> None:
    text = WORKFLOWS[1].read_text(encoding="utf-8")
    assert "Read selected issue" in text
    assert "build_workflow_dispatch_issue_event.py" in text
    assert "AUTODOC_EVENT_PATH:" in text
    assert "GITHUB_EVENT_PATH:" not in text


def test_copilot_is_optional_advisory_and_tool_denied() -> None:
    text = (
        ROOT / "templates/github/scripts/run_autodoc_copilot_advisory.py"
    ).read_text(encoding="utf-8")
    for marker in (
        "--no-ask-user",
        "--deny-tool=write",
        "--deny-tool=shell",
        '"usable_as_authority": False',
        "Do not modify it",
        "AUTODOC_COPILOT_REQUIRED",
        "check=False",
        "output_path.unlink(missing_ok=True)",
    ):
        assert marker in text
    assert "COPILOT_GITHUB_TOKEN" not in text
    assert "check=True" not in text


def test_authoritative_request_has_no_synthetic_issue_fallback() -> None:
    text = (
        ROOT / "templates/github/scripts/build_autodoc_authoritative_request.py"
    ).read_text(encoding="utf-8")
    assert "requires a positive issue number" in text
    assert "Untitled GitHub request" not in text
    assert "No description supplied." not in text
