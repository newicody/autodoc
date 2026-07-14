# Bundle GitHub pour `newicody/projects`

Ce répertoire est la source du bundle copié dans le dépôt privé de gestion. Les
fichiers situés ici ne constituent pas un mode projet actif dans Autodoc.

Le mode opératoire cumulatif est conservé dans [`INSTALLATION.md`](INSTALLATION.md).
Il doit être mis à jour avec chaque évolution utile de la copie, des Actions,
des variables, des secrets ou des vues.

Le bundle contient actuellement :

```text
.github/ISSUE_TEMPLATE/research.yml
.github/ISSUE_TEMPLATE/update.yml
.github/ISSUE_TEMPLATE/theme.yml
.github/ISSUE_TEMPLATE/config.yml
.github/workflows/autodoc-controlled-research.yml
scripts/build_workflow_dispatch_issue_event.py
scripts/run_workflow_dispatch_authoritative_request.py
scripts/reconcile_projectv2_configuration.py
scripts/project_copilot_advisory_fields.py
projectv2_views.json
INSTALLATION.md
PROJECT_BOARD_TEMPLATE.md
RESULT_UPDATE_PRESENTATION_CONTRACT.md
```

`transversal-event.yml` est retiré : une recherche peut déjà référencer
plusieurs groupes, tickets, résultats, dépôts, chemins, pièces jointes et URL.

Le workflow GitHub reste un producteur d'artefacts en lecture seule. Il ne
s'auto-autorise ni à publier l'avis Copilot, ni à modifier ProjectV2 :

```text
workflow_dispatch
→ demande autoritative
→ avis Copilot facultatif
→ manifeste corrélé
→ artefacts Actions
```

Après validation opérateur, deux adaptateurs indépendants rendent le retour
visible :

```text
Autodoc 0281
→ commentaire d'Issue contrôlé et idempotent

bundle copié dans newicody/projects
→ projection contrôlée du dernier état dans les champs ProjectV2
```

La configuration `projectv2_views.json` décrit les champs et les vues
`Recherches`, `Résultats`, `Copilot`, `Connaissances serveur`,
`Boîtes de thèmes`, `Historique` et `Tous`.

Le déclencheur automatique reste côté serveur local :

```text
ProjectV2 query-only → diff local → transition vers En cours
→ workflow_dispatch explicite dans newicody/projects
```

Pour activer Copilot dans `newicody/projects` :

```text
AUTODOC_COPILOT_ADVISORY_ENABLED=true
```

Aucun secret Copilot durable n'est attendu. La création des champs/vues et la
projection ProjectV2 utilisent un PAT classique distinct, uniquement lors
d'une opération explicitement approuvée.
