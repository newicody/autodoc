from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
REPORT = ROOT / (
    "PHASE0287_R7_R15_R2_R2_R2_PROJECTS_INSTALLATION_"
    "REMAINING_COMPATIBILITY_MARKERS_FIX_REPORT.md"
)
ARCH = ROOT / (
    "doc/architecture/PROJECTS_INSTALLATION_REMAINING_"
    "COMPATIBILITY_MARKERS_FIX_0287_R7_R15_R2_R2_R2.md"
)
DOT = ROOT / (
    "doc/architecture/PROJECTS_INSTALLATION_REMAINING_"
    "COMPATIBILITY_MARKERS_FIX_0287_R7_R15_R2_R2_R2.dot"
)
CHANGELOG = ROOT / (
    "doc/CHANGELOG_0287_R7_R15_R2_R2_R2_PROJECTS_INSTALLATION_"
    "REMAINING_COMPATIBILITY_MARKERS_FIX.md"
)
MANIFEST = ROOT / (
    "doc/manifests/MANIFEST_0287_R7_R15_R2_R2_R2_PROJECTS_"
    "INSTALLATION_REMAINING_COMPATIBILITY_MARKERS_FIX.md"
)


def test_remaining_cumulative_installation_markers_are_present() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    for marker in (
        "## Compatibilité cumulative 0287-r5-r2-r2",
        "publish_github_advisory_issue_comment_0281.py",
        "| `0284-r9` |",
        "verify_specialists_laboratories_live_path_evidence_0284.py",
    ):
        assert marker in text


def test_remaining_markers_do_not_break_locked_installation_invariants() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert len(text.splitlines()) < 380
    assert '--confirm-plan-digest "$PLAN_DIGEST"' in text
    assert text.index("AUTODOC_COPILOT_ADVISORY_ENABLED=false") < text.index(
        "AUTODOC_COPILOT_ADVISORY_ENABLED=true"
    )
    assert "### Compatibilité des anciens exemples — ne pas exécuter" in text


def test_remaining_markers_fix_deliverables_exist() -> None:
    for path in (REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
    assert not DOT.with_suffix(".svg").exists()
    report = REPORT.read_text(encoding="utf-8")
    for marker in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: false",
    ):
        assert marker in report
