from pathlib import Path

ROOT = Path(__file__).parents[2]
BUNDLE = ROOT / "templates/github/projects-repository"
INSTALLATION = BUNDLE / "INSTALLATION.md"
RUNBOOK = BUNDLE / "PROJECTS_BUNDLE_DRIFT_AUDIT.md"


def test_installation_returns_below_locked_budget() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert len(text.splitlines()) < 380
    for marker in (
        "Version du guide : `0287-r5-r1`.",
        "Extension de contrat Copilot : `0287-r7-r2`.",
        "Version actuelle du guide : `0287-r5`.",
        "mode opératoire cumulatif",
        "Le workflow ne publie pas lui-même son avis",
        "Cette valeur est le défaut d'installation",
        "Ne pas créer de secret `AUTODOC_COPILOT_TOKEN`",
        "ne déclenche aucun dispatch",
        "Ne pas utiliser `--delete`",
        "PROJECTS_BUNDLE_DRIFT_AUDIT.md",
    ):
        assert marker in text


def test_detailed_audit_moves_to_managed_runbook() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    for marker in (
        "projects_bundle_manifest.json",
        "audit_projects_bundle_drift.py",
        "copy_candidates",
        "safe_delete_candidates",
        "unknown_extra_files",
        "mutation_performed = false",
        "remote_access_performed = false",
        "rsync_delete_allowed = false",
    ):
        assert marker in text
