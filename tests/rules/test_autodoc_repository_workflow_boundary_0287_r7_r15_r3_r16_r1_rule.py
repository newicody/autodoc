from pathlib import Path


ROOT = Path(__file__).parents[2]
AUTODOC_WORKFLOW_DIRECTORY = ROOT / ".github" / "workflows"
PROJECTS_WORKFLOW_TEMPLATE = (
    ROOT
    / "templates"
    / "github"
    / "projects-repository"
    / ".github"
    / "workflows"
    / "autodoc-controlled-research.yml"
)


def test_autodoc_root_contains_no_active_actions_workflow() -> None:
    active = ()
    if AUTODOC_WORKFLOW_DIRECTORY.exists():
        active = tuple(
            sorted(
                path.relative_to(ROOT).as_posix()
                for path in AUTODOC_WORKFLOW_DIRECTORY.iterdir()
                if path.is_file()
                and path.suffix.casefold() in {".yml", ".yaml"}
            )
        )

    assert active == ()


def test_controlled_research_workflow_remains_in_projects_bundle() -> None:
    assert PROJECTS_WORKFLOW_TEMPLATE.is_file()

    readme = AUTODOC_WORKFLOW_DIRECTORY / "README.md"
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    assert "newicody/projects" in text
    assert "local Autodoc fetch/import" in text
