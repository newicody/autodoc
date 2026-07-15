from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)
RECONCILE = (
    ROOT
    / "templates/github/projects-repository/scripts/"
    "reconcile_projectv2_configuration.py"
)


def test_view_endpoint_uses_owner_login_after_content_repair() -> None:
    source = RECONCILE.read_text(encoding="utf-8")

    assert (
        'views_endpoint = '
        'f"users/{plan.owner}/projectsV2/{plan.number}/views"'
        in source
    )
    assert (
        'views_endpoint = '
        'f"users/{plan.user_id}/projectsV2/{plan.number}/views"'
        not in source
    )


def test_remaining_installation_markers_are_restored() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")

    for marker in (
        "Version actuelle du guide : `0287-r5`.",
        "AUTODOC_COPILOT_ADVISORY_ENABLED=true",
        "Après un premier dispatch validé sans Copilot",
        "| `0284-r9` |",
    ):
        assert marker in text

    assert "Version du guide : `0287-r5-r1`." in text
    assert "Ne pas utiliser `--delete`" in text
    assert "Ne pas créer de secret `AUTODOC_COPILOT_TOKEN`" in text
