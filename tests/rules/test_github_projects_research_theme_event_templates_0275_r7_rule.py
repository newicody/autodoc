from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "templates/github/projects-repository"
RESEARCH = BUNDLE / ".github/ISSUE_TEMPLATE/research.yml"
THEME = BUNDLE / ".github/ISSUE_TEMPLATE/theme.yml"
EVENT = BUNDLE / ".github/ISSUE_TEMPLATE/transversal-event.yml"
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
    assert "Les tickets sans thème" in board


def test_0275_r7_research_form_exposes_refinement_sources_and_exclusions() -> None:
    text = RESEARCH.read_text(encoding="utf-8")

    required = (
        "Affinage pour le prochain cycle",
        "Chercher sur : tickets et recherches",
        "Chercher sur : dépôts",
        "Chercher sur : documents, médias et liens",
        "Chercher sur : thèmes",
        "Plusieurs thèmes sélectionnés",
        "Exclure les recherches liées",
        "Lancer également une inférence sur un moteur externe",
        "Origine et liens hiérarchiques",
    )
    for phrase in required:
        assert phrase in text


def test_0275_r7_theme_and_transversal_event_keep_hierarchy_without_server_taxonomy() -> None:
    theme = THEME.read_text(encoding="utf-8")
    event = EVENT.read_text(encoding="utf-8")

    assert "Tickets de recherche englobés" in theme
    assert "Recherche spécifique sur ce thème" in theme
    assert "ne choisit\n        aucun laboratoire" in theme
    assert "Recherche d'origine" in event
    assert "Thèmes sélectionnés" in event
    assert "Événement parent ou précédent" in event
    assert "devient une recherche indépendante" in event


def test_0275_r7_workflow_is_explicit_read_only_and_not_issue_triggered() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    trigger_block = text.split("permissions:", 1)[0]

    assert "workflow_dispatch:" in trigger_block
    assert "\n  issues:" not in trigger_block
    assert "requested_status:" in text
    assert "request_mode:" in text
    assert "parent_event_ref:" in text
    assert "issues: read" in text
    assert "contents: read" in text
    assert "write" not in text
    assert "AUTODOC_GITHUB_TOKEN" not in text
    assert "AUTODOC_PROJECT_TOKEN" not in text
