from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
INSTALLATION = (
    ROOT / "templates/github/projects-repository/INSTALLATION.md"
)


def test_simplified_projects_installation_keeps_compatibility_markers() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")

    for marker in (
        "Installation cumulative de `newicody/projects`",
        "mode opératoire cumulatif",
        "Le workflow ne publie pas lui-même son avis",
        "Cette valeur est le défaut d'installation",
        "Ne pas créer de secret `AUTODOC_COPILOT_TOKEN`",
        "ne déclenche aucun dispatch",
    ):
        assert marker in text

    current = re.search(
        r"^Version du guide : `(?P<version>[^`]+)`\.$",
        text,
        flags=re.MULTILINE,
    )
    assert current is not None
    assert current.group("version") == "0287-r5-r1"

    for historical in (
        "Version du guide : `0286-r4`.",
        "Version du guide : `0286-r3`.",
        "Version du guide : `0284-r9`.",
        "Version du guide : `0284-r1-r5`.",
    ):
        assert historical in text

    assert text.index("Version du guide : `0287-r5-r1`.") < text.index(
        "Version du guide : `0286-r4`."
    )
    assert len(text.splitlines()) < 380
