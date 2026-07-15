from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPLY = (
    ROOT
    / "tools/apply_specialist_capability_growth_projects_projection_0286.py"
)
READBACK = (
    ROOT
    / "tools/check_specialist_capability_growth_projects_readback_0286.py"
)
FIXTURE = (
    ROOT
    / "tools/"
    "build_specialist_capability_growth_projects_readback_fixture_0286.py"
)
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)


def test_r6_cli_persists_execution_evidence() -> None:
    text = APPLY.read_text(encoding="utf-8")
    assert '"--output"' in text
    assert "_write_report(report, args.output)" in text


def test_r7_cli_has_actionable_artifact_preflight() -> None:
    text = READBACK.read_text(encoding="utf-8")
    assert "_require_input_file" in text
    assert "The r7 verifier consumes artifacts" in text
    assert "does not create or publish" in text


def test_fixture_is_explicitly_local_only() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    assert "fixture_only" in text
    assert "must never be passed" in text
    assert "real_github_publication_proven" in text
    assert "subprocess" not in text
    assert "gh api" not in text


def test_projects_installation_remains_unchanged() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0286-r4`." in text
    assert "Ne pas utiliser `--delete`" in text
