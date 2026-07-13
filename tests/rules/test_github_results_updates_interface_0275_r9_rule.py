from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "templates/github/projects-repository"
RESEARCH = BUNDLE / ".github/ISSUE_TEMPLATE/research.yml"
UPDATE = BUNDLE / ".github/ISSUE_TEMPLATE/update.yml"
GROUP = BUNDLE / ".github/ISSUE_TEMPLATE/theme.yml"
LEGACY_EVENT = BUNDLE / ".github/ISSUE_TEMPLATE/transversal-event.yml"
BOARD = BUNDLE / "PROJECT_BOARD_TEMPLATE.md"
CONTRACT = BUNDLE / "RESULT_UPDATE_PRESENTATION_CONTRACT.md"


def test_0275_r9_research_separates_parent_from_linked_results() -> None:
    text = RESEARCH.read_text(encoding="utf-8")

    assert "Résultat parent facultatif" in text
    assert "Ce champ n'est pas une liste de sources." in text
    assert "Résultats liés" in text
    assert "ne créent aucune carte dupliquée" in text
    assert "Groupes ou thèmes liés" in text
    assert "Tickets liés" in text
    assert "Dépôts et données internes" in text
    assert "Pièces jointes et liens externes" in text
    assert "newicody/autodoc" in text
    assert "Ne jamais sélectionner" in text


def test_0275_r9_update_targets_existing_result_and_is_append_only() -> None:
    form = UPDATE.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")

    assert "Résultat cible" in form
    assert "required: true" in form
    assert "Nouveaux paramètres" in form
    assert "Nouvelles pièces jointes et nouveaux liens" in form
    assert "Actualisation append-only" in contract
    assert "## UPDATE — 2026-07-13 23:42 Europe/Paris" in contract
    assert "timestamp canonique" in contract
    assert "commentaires UPDATE successifs" in contract


def test_0275_r9_board_only_shows_current_results_in_main_view() -> None:
    text = BOARD.read_text(encoding="utf-8")

    assert "Vue `Résultats`" in text
    assert "Affichage = Résultat courant" in text
    assert "Vue `Actions serveur`" in text
    assert "Affichage = Action" in text
    assert "Vue `Historique`" in text
    assert "Affichage = Historique" in text
    assert "Vue `Groupes`" in text
    assert "Affichage = Groupe" in text
    assert "Résumé, Avis Copilot, Serveur, Copilot, Dernière mise à jour" in text
    assert "panneau latéral natif" in text


def test_0275_r9_removes_redundant_transversal_form() -> None:
    group = GROUP.read_text(encoding="utf-8")

    assert LEGACY_EVENT.exists() is False
    assert "Nouveau groupe de contexte" in group
    assert "Il n'est ni un" in group
    assert "résultat, ni une action" in group


def test_0275_r9_is_interface_only() -> None:
    board = BOARD.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")

    assert "n'ajoute encore aucune publication ou mutation GitHub" in board
    assert "phase ultérieure" in contract
    assert "Scheduler" not in contract
    assert "SQL" not in contract
    assert "Qdrant" not in contract
