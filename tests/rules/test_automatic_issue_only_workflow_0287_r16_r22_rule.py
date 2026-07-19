from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows"
    / "autodoc-controlled-research.yml"
)


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_initial_research_workflow_has_one_automatic_trigger() -> None:
    text = _workflow()

    assert re.search(
        r"(?m)^on:\n  issues:\n    types:\n      - opened\n",
        text,
    )
    assert not re.search(
        r"(?m)^  workflow_dispatch:\s*$",
        text,
    )
    assert not re.search(
        r"(?m)^  (schedule|repository_dispatch|"
        r"project_v2_item|push|pull_request):\s*$",
        text,
    )


def test_issue_event_is_the_only_runtime_source() -> None:
    text = _workflow()

    assert "github.event_name == 'issues'" in text
    assert "github.event.action == 'opened'" in text
    assert "${{ github.event.issue.number }}" in text
    assert "inputs." not in text
    assert "github.event_name == 'workflow_dispatch'" not in text


def test_initial_research_intention_is_constant() -> None:
    text = _workflow()

    assert (
        'AUTODOC_REQUESTED_STATUS_RESOLVED: "Recherche"'
        in text
    )
    assert (
        'AUTODOC_REQUEST_MODE_RESOLVED: "initial"'
        in text
    )
    assert (
        'AUTODOC_PARENT_EVENT_REF_RESOLVED: ""'
        in text
    )
    assert (
        'AUTODOC_COPILOT_REQUIRED_RESOLVED: "true"'
        in text
    )


def test_copilot_is_required_without_repository_enable_variable() -> None:
    text = _workflow()

    assert "AUTODOC_COPILOT_ADVISORY_ENABLED" not in text
    assert "Restore pinned Copilot CLI" in text
    assert "Install pinned Copilot CLI on cache miss" in text
    assert "Verify pinned Copilot CLI" in text
    assert "Build optional Copilot advisory" in text
    assert (
        "steps.autodoc-copilot-cli-cache.outputs."
        "cache-hit != 'true'"
        in text
    )


def test_workflow_keeps_issue_shape_filter_and_three_uploads() -> None:
    text = _workflow()

    assert "startsWith(github.event.issue.title, '[Recherche] ')" in text
    assert "### Question ou objectif" in text
    assert "### Résultat attendu" in text
    assert text.count("uses: actions/upload-artifact@v7") == 3
    assert "Upload authoritative request" in text
    assert "Upload optional Copilot advisory" in text
    assert "Upload manifest" in text
