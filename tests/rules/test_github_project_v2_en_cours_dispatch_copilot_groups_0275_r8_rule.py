from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    "autodoc-controlled-research.yml"
)
BOARD = (
    ROOT
    / "templates/github/projects-repository/PROJECT_BOARD_TEMPLATE.md"
)
README = ROOT / "templates/github/projects-repository/README.md"
CONFIG = ROOT / "config/github_project_v2_query_only.example.ini"
CONTRACT = (
    ROOT
    / "src/context/github_project_v2_en_cours_dispatch_0275_r8.py"
)
DISPATCH = (
    ROOT
    / "tools/dispatch_github_project_v2_en_cours_transitions_0275_r8.py"
)
RUN_ONCE = (
    ROOT
    / "tools/run_github_project_v2_en_cours_dispatch_once_0275_r8.py"
)


def test_0275_r8_workflow_activates_copilot_without_durable_secret() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "copilot-requests: write" in text
    assert "GITHUB_TOKEN: ${{ github.token }}" in text
    assert "AUTODOC_COPILOT_TOKEN" not in text
    assert "COPILOT_GITHUB_TOKEN" not in text
    assert "contents: write" not in text
    assert "issues: write" not in text
    assert "actions: write" not in text


def test_0275_r8_board_keeps_theme_rows_and_en_cours_command() -> None:
    text = BOARD.read_text(encoding="utf-8")

    assert "Group by     : Thème" in text
    assert "Vue `Résultats`" in text
    assert "Vue `Actions serveur`" in text
    assert "Recherche      → En cours" in text
    assert "Développement → En cours" in text
    assert "Production     → En cours" in text
    assert "Group by     : Parent issue" not in text
    assert "Vue `Boîtes de thèmes`" not in text


def test_0275_r8_scopes_dispatch_without_relaxing_query_only_snapshot() -> None:
    text = CONFIG.read_text(encoding="utf-8")

    assert "[safety]" in text
    assert "query_only = true" in text
    assert "graphql_mutation_allowed = false" in text
    assert "allow_workflow_dispatch = false" in text
    assert "allow_remote_mutation = false" in text
    assert "[workflow_dispatch]" in text
    assert "repository = newicody/projects" in text
    assert "workflow_name = autodoc-controlled-research.yml" in text
    assert "target_status = En cours" in text
    assert "allow_workflow_dispatch = true" in text
    assert "allow_remote_mutation = true" in text


def test_0275_r8_reuses_0272_and_keeps_scheduler_untouched() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    dispatch = DISPATCH.read_text(encoding="utf-8")
    run_once = RUN_ONCE.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    assert "consumes_existing_0272_change_set" in contract
    assert "scheduler_modified" in contract
    assert "scheduler_run_modified" in contract
    assert "run_github_project_v2_query_only_snapshot_0272.py" in run_once
    assert "detect_github_project_v2_snapshot_changes_0272.py" in run_once
    assert "while " not in run_once
    assert "urlopen" in dispatch
    assert "ProjectV2 query-only → diff local" in readme
