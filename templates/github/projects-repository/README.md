# Bundle GitHub pour `newicody/projects`

Ce répertoire est copié dans le dépôt privé de gestion.

Il contient :

```text
.github/ISSUE_TEMPLATE/research.yml
.github/ISSUE_TEMPLATE/update.yml
.github/ISSUE_TEMPLATE/theme.yml
.github/ISSUE_TEMPLATE/config.yml
.github/workflows/autodoc-controlled-research.yml
PROJECT_BOARD_TEMPLATE.md
RESULT_UPDATE_PRESENTATION_CONTRACT.md
```

`transversal-event.yml` est retiré : une recherche peut déjà référencer
plusieurs groupes, tickets, résultats, dépôts, chemins, pièces jointes et URL.

Le workflow ne modifie encore ni les issues, ni le Project. Il produit la
demande autoritative, l'avis Copilot facultatif et leur manifeste.

Le déclencheur automatique reste côté serveur local :

```text
ProjectV2 query-only → diff local → transition vers En cours
→ workflow_dispatch explicite
```

Pour activer Copilot dans `newicody/projects` :

```text
AUTODOC_COPILOT_ADVISORY_ENABLED = true
```

Aucun secret Copilot durable n'est attendu.
