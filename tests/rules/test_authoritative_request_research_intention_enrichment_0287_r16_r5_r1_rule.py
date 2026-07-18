from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    / "autodoc-controlled-research.yml"
)
ENRICHER = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    / "enrich_authoritative_request_research_intention.py"
)
BUILDER = ROOT / "templates/github/scripts/build_autodoc_authoritative_request.py"


def test_workflow_enriches_before_copilot_and_manifest() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    step = "Preserve controlled research intention"
    script = "enrich_authoritative_request_research_intention.py"

    assert step in workflow
    assert script in workflow
    assert workflow.index(step) < workflow.index("Restore pinned Copilot CLI")
    assert workflow.index(step) < workflow.index("Build linking manifest")
    assert "AUTODOC_EVENT_PATH:" in workflow
    assert "AUTODOC_REQUEST:" in workflow


def test_enrichment_is_separate_from_the_generic_builder() -> None:
    enricher = ENRICHER.read_text(encoding="utf-8")
    builder = BUILDER.read_text(encoding="utf-8")

    for marker in (
        '"requested_status"',
        '"request_mode"',
        '"parent_event_ref"',
        '"missipy.github.authoritative_request.v1"',
        "authoritative metadata collision",
    ):
        assert marker in enricher

    assert "enrich_authoritative_request_research_intention" not in builder
    assert "Scheduler" not in enricher
    assert "qdrant" not in enricher.lower()
    assert "psycopg" not in enricher.lower()
    assert "subprocess" not in enricher
