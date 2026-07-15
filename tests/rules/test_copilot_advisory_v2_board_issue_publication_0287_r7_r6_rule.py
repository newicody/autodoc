from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ISSUE = ROOT / "src/context/github_copilot_advisory_v2_issue_publication_0287.py"
ISSUE_TOOL = ROOT / "tools/publish_github_copilot_advisory_v2_issue_comment_0287.py"
PREVIEW = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    "build_copilot_advisory_v2_publication_preview.py"
)
FIELDS = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    "project_copilot_advisory_v2_fields.py"
)


def test_v2_publication_is_versioned_and_keeps_v1_semantics_separate() -> None:
    issue = ISSUE.read_text(encoding="utf-8")
    preview = PREVIEW.read_text(encoding="utf-8")
    fields = FIELDS.read_text(encoding="utf-8")
    assert "copilot_advisory_publication_preview.v2" in issue
    assert "copilot_advisory_v2_issue_publication_plan.v1" in issue
    assert "copilot_projectv2_projection_plan.v2" in fields
    assert "copilot_advisory.v2" in preview
    assert "summary" not in preview.split("return {", 1)[1].split("}", 1)[0]


def test_board_projection_does_not_invent_route_or_confidence() -> None:
    fields = FIELDS.read_text(encoding="utf-8")
    assert "route_field_mutated\": False" in fields
    assert "confidence_field_mutated\": False" in fields
    mutation_section = fields.split("mutations = (", 1)[1].split("except (", 1)[0]
    assert '"route_field"' not in mutation_section
    assert '"confidence_field"' not in mutation_section
    assert '"summary_field"' in mutation_section


def test_remote_mutations_keep_explicit_gates_and_readback() -> None:
    issue_tool = ISSUE_TOOL.read_text(encoding="utf-8")
    fields = FIELDS.read_text(encoding="utf-8")
    for marker in (
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_ISSUE_PUBLICATION_ALLOWED",
        "confirm-plan-digest mismatch",
        "readback_verified",
    ):
        assert marker in issue_tool
    for marker in (
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_PROJECT_PROJECTION_ALLOWED",
        "confirm-plan-digest mismatch",
        "_verify_readback",
        "readback_verified=True",
    ):
        assert marker in fields


def test_phase_delivers_systematic_artifacts_and_updates_installation() -> None:
    report = ROOT / "PHASE0287_R7_R6_COPILOT_ADVISORY_V2_BOARD_ISSUE_PUBLICATION_REPORT.md"
    architecture = ROOT / "doc/architecture/COPILOT_ADVISORY_V2_BOARD_ISSUE_PUBLICATION_0287_R7_R6.md"
    manifest = ROOT / "doc/manifests/MANIFEST_0287_R7_R6_COPILOT_ADVISORY_V2_BOARD_ISSUE_PUBLICATION.md"
    guide = ROOT / "templates/github/projects-repository/INSTALLATION.md"
    runbook = ROOT / "templates/github/projects-repository/COPILOT_ADVISORY_V2.md"
    current = ROOT / "doc/README_CURRENT.md"
    for path in (report, architecture, manifest):
        assert path.exists()
    assert "0287-r7-r6" in guide.read_text(encoding="utf-8")
    assert "Publication v2 sur le board et l’Issue" in runbook.read_text(encoding="utf-8")
    current_text = current.read_text(encoding="utf-8")
    assert "controlled adapters implemented" in current_text
    assert "publication-surface readback/replay" in current_text
