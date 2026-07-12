# Bundle GitHub pour `newicody/projects`

Ce répertoire est copié dans le dépôt privé de gestion.

Il contient :

```text
.github/ISSUE_TEMPLATE/research.yml
.github/ISSUE_TEMPLATE/theme.yml
.github/ISSUE_TEMPLATE/transversal-event.yml
.github/ISSUE_TEMPLATE/config.yml
.github/workflows/autodoc-controlled-research.yml
PROJECT_BOARD_TEMPLATE.md
```

Le workflow ne modifie ni les issues, ni le Project, ni les champs `Status` ou
`Thème`. Il produit la demande autoritative, l'avis Copilot facultatif et leur
manifeste.

Le déclencheur automatique reste côté serveur local :

```text
ProjectV2 query-only → diff local → transition vers En cours
→ workflow_dispatch explicite
```

Pour activer Copilot dans `newicody/projects`, définir la variable Actions :

```text
AUTODOC_COPILOT_ADVISORY_ENABLED = true
```

Le workflow utilise le `GITHUB_TOKEN` éphémère avec la permission
`copilot-requests: write`; aucun secret Copilot durable n'est attendu.
