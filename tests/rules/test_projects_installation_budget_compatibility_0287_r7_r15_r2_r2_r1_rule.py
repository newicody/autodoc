from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"
REPORT = ROOT / (
    "PHASE0287_R7_R15_R2_R2_R1_PROJECTS_INSTALLATION_"
    "BUDGET_COMPATIBILITY_FIX_REPORT.md"
)
ARCH = ROOT / (
    "doc/architecture/PROJECTS_INSTALLATION_BUDGET_"
    "COMPATIBILITY_FIX_0287_R7_R15_R2_R2_R1.md"
)
DOT = ROOT / (
    "doc/architecture/PROJECTS_INSTALLATION_BUDGET_"
    "COMPATIBILITY_FIX_0287_R7_R15_R2_R2_R1.dot"
)
CHANGELOG = ROOT / (
    "doc/CHANGELOG_0287_R7_R15_R2_R2_R1_PROJECTS_"
    "INSTALLATION_BUDGET_COMPATIBILITY_FIX.md"
)
MANIFEST = ROOT / (
    "doc/manifests/MANIFEST_0287_R7_R15_R2_R2_R1_"
    "PROJECTS_INSTALLATION_BUDGET_COMPATIBILITY_FIX.md"
)


def test_installation_respects_locked_budget_and_cumulative_markers() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert len(text.splitlines()) < 380
    for marker in (
        "Version du guide : `0287-r5-r1`.",
        "Version actuelle du guide : `0287-r5`.",
        "Version du guide : `0286-r4`.",
        "Version du guide : `0286-r3`.",
        "Version du guide : `0284-r9`.",
        "Version du guide : `0284-r1-r5`.",
        "0287-r5-r2-r2",
        "Révisions spécialistes",
        "COPILOT_ADVISORY_PUBLICATION.md",
        "COPILOT_ADVISORY_V2.md",
    ):
        assert marker in text


def test_real_digest_command_precedes_forbidden_legacy_examples() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    safe = '--confirm-plan-digest "$PLAN_DIGEST"'
    heading = "### Compatibilité des anciens exemples — ne pas exécuter"
    placeholder = "--confirm-plan-digest '<PLAN_DIGEST>'"
    empty = "--confirm-plan-digest ''"
    assert text.index(safe) < text.index(heading)
    assert text.count(placeholder) == 1
    assert text.count(empty) == 1
    assert text.index(heading) < text.index(placeholder)
    assert text.index(heading) < text.index(empty)


def test_copilot_safe_default_precedes_optional_activation() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    disabled = "AUTODOC_COPILOT_ADVISORY_ENABLED=false"
    enabled = "AUTODOC_COPILOT_ADVISORY_ENABLED=true"
    assert text.index(disabled) < text.index(enabled)
    assert "Cette valeur est le défaut d'installation" in text
    assert "Après un premier dispatch validé sans Copilot" in text


def test_r15_readiness_and_short_preview_path_are_preserved() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    for marker in (
        "/tmp/projectv2-configuration-preview.json",
        "jq -r '.plan_digest // empty'",
        "check_projects_bundle_readiness.py",
        "projectv2_exact",
        "authoritative_ready",
        "copilot_ready",
        "manual_dispatch_only",
        "github_owned_allowed",
        "love_actions_closed_loop.example.ini",
        "Preview final sans identifiants ProjectV2 manuels",
        "PROJECT_ITEM_ID",
        "python tools/run_love_actions_closed_loop_0287.py",
        "--candidate-decision promote",
        "Le preview ne réalise aucune mutation distante",
    ):
        assert marker in text


def test_deliverables_and_code_rule_review_exist() -> None:
    for path in (REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path
    assert not DOT.with_suffix(".svg").exists()
    report = REPORT.read_text(encoding="utf-8")
    for marker in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: false",
        "github_api_added: false",
    ):
        assert marker in report
