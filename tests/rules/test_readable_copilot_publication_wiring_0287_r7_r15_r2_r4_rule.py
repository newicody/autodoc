from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ROOT / "src/context/readable_copilot_publication_wiring_0287.py"
TOOL = ROOT / "tools/publish_readable_copilot_advisory_v2_0287.py"


def test_domain_is_pure_and_keeps_authority_boundaries() -> None:
    source = DOMAIN.read_text(encoding="utf-8")
    assert "request_authoritative" in source
    assert "advisory_is_authority" in source
    assert "preview_required" in source
    assert "subprocess" not in source
    assert "requests" not in source
    assert "Scheduler" not in source


def test_tool_reuses_existing_issue_and_projectv2_adapters() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "publish_github_copilot_advisory_v2_issue_comment_0287.py" in source
    assert "project_copilot_advisory_v2_fields.py" in source
    assert "plan_copilot_v2_field_projection" in source
    assert "execute_copilot_v2_field_projection" in source
    assert "plan_copilot_advisory_v2_issue_publication" in source


def test_remote_execution_requires_all_gates_and_combined_digest() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for marker in (
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_ISSUE_PUBLICATION_ALLOWED",
        "AUTODOC_PROJECT_PROJECTION_ALLOWED",
        "confirm-plan-digest mismatch",
        "issue_action",
        "project_action",
        "readback_verified",
    ):
        assert marker in source
