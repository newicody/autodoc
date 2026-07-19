from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "templates/github/projects-repository"
RESEARCH = BUNDLE / ".github/ISSUE_TEMPLATE/research.yml"
UPDATE = BUNDLE / ".github/ISSUE_TEMPLATE/update.yml"
THEME = BUNDLE / ".github/ISSUE_TEMPLATE/theme.yml"
LEGACY_EVENT = BUNDLE / ".github/ISSUE_TEMPLATE/transversal-event.yml"
WORKFLOW = BUNDLE / ".github/workflows/autodoc-controlled-research.yml"
BOARD = BUNDLE / "PROJECT_BOARD_TEMPLATE.md"
R6_MODEL = ROOT / "doc/architecture/GITHUB_RESEARCH_KANBAN_OPERATOR_MODEL_0275_R6.md"


def test_0275_r7_uses_default_status_field_and_optional_theme_rows() -> None:
    model = R6_MODEL.read_text(encoding="utf-8")
    board = BOARD.read_text(encoding="utf-8")

    assert "colonne            = Status et intention opérateur" in model
    assert "Status\nThème" in model
    assert "Column field : Status" in board
    assert "Group by     : Thème" in board
    assert "Thème" in board


def test_0275_r7_research_form_exposes_selected_source_references() -> None:
    text = RESEARCH.read_text(encoding="utf-8")

    required = (
        "Question ou objectif",
        "Résultat parent facultatif",
        "Résultats liés",
        "Groupes ou thèmes liés",
        "Tickets liés",
        "Dépôts et données internes",
        "Pièces jointes et liens externes",
        "Paramètres et précisions",
        "Produire également un avis Copilot séparé",
    )
    for phrase in required:
        assert phrase in text


def test_0275_r7_group_and_update_forms_replace_transversal_event() -> None:
    theme = THEME.read_text(encoding="utf-8")
    update = UPDATE.read_text(encoding="utf-8")

    assert "Nouveau groupe de contexte" in theme
    assert "ni un" in theme
    assert "résultat, ni une action de traitement" in theme
    assert "Actualiser un résultat" in update
    assert "Résultat cible" in update
    assert "Nouveaux paramètres" in update
    assert LEGACY_EVENT.exists() is False


def test_0275_r7_workflow_keeps_read_only_permissions_with_automatic_trigger() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    trigger_block = text.split("permissions:", 1)[0]

    assert "workflow_dispatch:" not in trigger_block
    assert "\n  issues:" in trigger_block
    assert "types:\n      - opened" in trigger_block
    assert "inputs." not in text
    assert "github.repository == 'newicody/projects'" in text
    assert "startsWith(github.event.issue.title, '[Recherche] ')" in text
    assert 'AUTODOC_REQUESTED_STATUS_RESOLVED: "Recherche"' in text
    assert 'AUTODOC_REQUEST_MODE_RESOLVED: "initial"' in text
    assert 'AUTODOC_PARENT_EVENT_REF_RESOLVED: ""' in text
    assert "issues: read" in text
    assert "contents: read" in text
    assert "copilot-requests: write" in text
    assert "contents: write" not in text
    assert "issues: write" not in text
    assert "actions: write" not in text
    assert "AUTODOC_GITHUB_TOKEN" not in text
    assert "AUTODOC_PROJECT_TOKEN" not in text
    assert "AUTODOC_COPILOT_TOKEN" not in text
    assert "GITHUB_TOKEN: ${{ github.token }}" in text
