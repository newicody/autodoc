from pathlib import Path

from context.specialist_capability_growth_projects_operator_workflow_reuse_audit_0286 import (
    DEVELOPMENT_PHASES,
    REQUIRED_REUSE_SURFACES,
    audit_specialist_capability_growth_projects_operator_workflow_reuse,
)

ROOT = Path(__file__).resolve().parents[2]
TOOL = (
    ROOT
    / "tools/apply_specialist_capability_growth_projects_projection_0286.py"
)
AUDIT = (
    ROOT
    / "src/context/"
    "specialist_capability_growth_projects_operator_workflow_reuse_audit_0286.py"
)
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_r6_cli_satisfies_the_existing_reuse_audit_markers() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert "--execute" in text
    assert "--confirm-plan-digest" in text
    assert "gh api" in text


def test_r6_cli_is_preview_first_and_digest_verified() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert "Preview is the default" in text
    assert "recompute_plan_digest" in text
    assert "plan_digest mismatch" in text
    assert "if args.execute" in text


def test_r6_cli_reuses_subprocess_gh_without_new_http_client() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert "subprocess.run" in text
    for forbidden in ("import requests", "import httpx", "import urllib"):
        assert forbidden not in text


def test_audit_can_advance_to_r7_after_cli_alignment() -> None:
    audit = AUDIT.read_text(encoding="utf-8")
    assert (
        '"tools/apply_specialist_capability_growth_projects_projection_0286.py"'
        in audit
    )
    assert (
        "0286-r7-specialist-capability-growth-projects-readback-readiness"
        in audit
    )


def test_projects_installation_remains_at_r4() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0286-r4`." in text
    assert "Ne pas utiliser `--delete`" in text


def test_actual_reuse_audit_advances_from_r6_to_r7() -> None:
    markers_by_path: dict[str, list[str]] = {}

    def add(path: str, markers: tuple[str, ...]) -> None:
        markers_by_path.setdefault(path, []).extend(markers)

    for requirement in REQUIRED_REUSE_SURFACES:
        add(requirement.path, requirement.markers)

    # Complete r2 through r5 using their declared markers.
    for phase in DEVELOPMENT_PHASES[:4]:
        for requirement in phase.requirements:
            add(requirement.path, requirement.markers)

    # Use the real r6 CLI content, not synthetic markers.
    r6_path = (
        "tools/apply_specialist_capability_growth_projects_projection_0286.py"
    )
    markers_by_path[r6_path] = [TOOL.read_text(encoding="utf-8")]

    sources = {
        path: "\n".join(markers)
        for path, markers in markers_by_path.items()
    }
    result = (
        audit_specialist_capability_growth_projects_operator_workflow_reuse(
            sources
        )
    )

    assert (
        "0286-r6-specialist-capability-growth-projects-operator-authorized-adapter"
        in result.completed_phases
    )
    assert result.next_recommended_patch == (
        "0286-r7-specialist-capability-growth-projects-readback-readiness"
    )
