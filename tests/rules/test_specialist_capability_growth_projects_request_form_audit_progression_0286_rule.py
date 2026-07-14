from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_R2_RULE = (
    ROOT
    / "tests/rules/test_specialist_capability_growth_projects_review_projection_0286_rule.py"
)
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
REPORT = ROOT / "PHASE0286_R3_R1_REQUEST_FORM_AUDIT_PROGRESSION_RULE_FIX_REPORT.md"
ARCHITECTURE = (
    ROOT
    / "doc/architecture/"
    "SPECIALIST_CAPABILITY_GROWTH_REQUEST_FORM_AUDIT_PROGRESSION_RULE_FIX_0286.md"
)
GRAPH = (
    ROOT
    / "doc/architecture/"
    "SPECIALIST_CAPABILITY_GROWTH_REQUEST_FORM_AUDIT_PROGRESSION_RULE_FIX_0286.dot"
)
CHANGELOG = ROOT / "doc/CHANGELOG_0286_R3_R1_REQUEST_FORM_AUDIT_PROGRESSION_RULE_FIX.md"
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0286_R3_R1_REQUEST_FORM_AUDIT_PROGRESSION_RULE_FIX.md"
)


def test_historical_r2_progression_rule_is_cumulative() -> None:
    source = HISTORICAL_R2_RULE.read_text(encoding="utf-8")

    assert "def test_reuse_audit_reaches_or_completes_r3" in source
    assert "r3_patch in result.completed_phases" in source
    assert "result.next_recommended_patch == r3_patch" in source


def test_fix_deliverables_exist() -> None:
    for path in (REPORT, ARCHITECTURE, GRAPH, CHANGELOG, MANIFEST):
        assert path.is_file(), path


def test_projects_installation_remains_on_r3() -> None:
    source = INSTALLATION.read_text(encoding="utf-8")

    assert "Version du guide : `0286-r3`." in source
    assert "specialist-capability-growth.yml" in source
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in source
    assert "Ne pas utiliser `--delete`" in source
