from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
RUNBOOK = ROOT / "templates/github/projects-repository/COPILOT_ADVISORY_V2.md"


def test_installation_stays_below_the_locked_line_budget() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert len(text.splitlines()) < 380
    assert "0287-r7-r6" in text
    assert "COPILOT_ADVISORY_V2.md" in text


def test_detailed_r6_operations_live_in_the_copilot_v2_runbook() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    for marker in (
        "build_copilot_advisory_v2_publication_preview.py",
        "project_copilot_advisory_v2_fields.py",
        "publish_github_copilot_advisory_v2_issue_comment_0287.py",
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_PROJECT_PROJECTION_ALLOWED",
        "AUTODOC_ISSUE_PUBLICATION_ALLOWED",
        "--confirm-plan-digest",
        "readback",
    ):
        assert marker in text


def test_installation_keeps_cumulative_safety_markers() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    for marker in (
        "Version du guide : `0287-r5-r1`.",
        "Version actuelle du guide : `0287-r5`.",
        "Ne pas utiliser `--delete`",
        "Ne pas créer de secret `AUTODOC_COPILOT_TOKEN`",
        "ne déclenche aucun dispatch",
    ):
        assert marker in text
