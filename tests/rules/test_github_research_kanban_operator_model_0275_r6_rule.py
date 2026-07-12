from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODEL = (
    ROOT
    / "doc/architecture/GITHUB_RESEARCH_KANBAN_OPERATOR_MODEL_0275_R6.md"
)
RUNBOOK = (
    ROOT
    / "doc/runbooks/INSTALL_GITHUB_RESEARCH_KANBAN_0275_R6.md"
)


def test_0275_r6_locks_human_facing_kanban_model() -> None:
    text = MODEL.read_text(encoding="utf-8")

    required = (
        "ligne facultative = Thème",
        "carte              = ticket de recherche durable",
        "colonne            = Status et intention opérateur",
        "cycle              = nouvelle exécution du même ticket",
        "Recherche",
        "En cours",
        "Terminé",
        "Développement",
        "Production",
        "Drop",
        "Une relance ne crée pas automatiquement une nouvelle issue",
        "Une recherche peut rester sans thème.",
    )
    for phrase in required:
        assert phrase in text


def test_0275_r6_locks_context_exclusion_semantics() -> None:
    text = MODEL.read_text(encoding="utf-8")

    required = (
        "tout élément historique reste disponible",
        "exclusions applicables uniquement au prochain",
        "Une exclusion ne supprime rien.",
        "La question d'origine et la demande courante restent toujours",
        "Exclure le résultat du cycle précédent",
        "Exclure les recherches liées",
        "Utiliser un contexte minimal",
    )
    for phrase in required:
        assert phrase in text


def test_0275_r6_keeps_server_architecture_out_of_project_fields() -> None:
    text = MODEL.read_text(encoding="utf-8")

    assert "Le modèle minimal contient uniquement" in text
    assert "Status\nThème" in text
    assert "Aucune vue ne doit refléter l'architecture interne du serveur." in text
    assert "scheduler_modified: false" in text
    assert "scheduler_run_modified: false" in text
    assert "remote_mutation_added: false" in text
    assert "non_stdlib_dependencies_added: false" in text


def test_0275_r6_installation_is_preparatory_and_safe() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    required = (
        "newicody/projects",
        "newicody/autodoc",
        "Ne pas activer encore les déclenchements de colonnes",
        "ne pas ajouter de token d'écriture",
        "ne pas installer de service OpenRC",
        "column_trigger_runtime_installed = false",
        "github_write_token_required = false",
        "openrc_service_installed = false",
        "Arrêter la série au premier échec.",
    )
    for phrase in required:
        assert phrase in text
