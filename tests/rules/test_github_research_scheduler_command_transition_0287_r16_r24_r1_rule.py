from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_typed_command_core_has_no_internal_storage_or_io() -> None:
    path = ROOT / "src/context/github_research_scheduler_command_0287.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert "class SchedulerCommand" in source
    assert "class AuthorizedSchedulerCommand(SchedulerCommand)" in source
    assert "class GitHubResearchSchedulerCommand(AuthorizedSchedulerCommand)" in source
    assert "class GitHubResearchSchedulerCommandStore(Protocol)" in source
    assert "class ResearchExecutionBudget" in source

    forbidden_imports = {"json", "pathlib", "os", "sqlite3"}
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(forbidden_imports)

    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "open" not in calls
    assert "Path" not in calls


def test_transition_docs_make_r16_r24_non_canonical() -> None:
    architecture = (
        ROOT
        / "doc/architecture/GITHUB_RESEARCH_AUTHORIZED_INTAKE_LOCAL_QUEUE_0287.md"
    ).read_text(encoding="utf-8")
    readme = (
        ROOT / "templates/github/projects-repository/README_INSTALLATION.md"
    ).read_text(encoding="utf-8")
    legacy_tool = (
        ROOT / "tools/queue_authorized_github_research_scheduler_intake_0287.py"
    ).read_text(encoding="utf-8")

    assert "non canonique" in architecture
    assert "PostgreSQL" in architecture
    assert "Ne plus lancer" in readme
    assert "typed-command-ready-for-sql" in readme
    assert "--allow-legacy-filesystem-handoff" in legacy_tool
