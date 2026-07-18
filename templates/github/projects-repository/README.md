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
.github/ISSUE_TEMPLATE/specialist-capability-growth.yml
.github/ISSUE_TEMPLATE/config.yml
.github/workflows/autodoc-controlled-research.yml
scripts/audit_projects_bundle_drift.py
scripts/build_copilot_advisory_publication_preview.py
scripts/build_copilot_advisory_v2_publication_preview.py
scripts/build_human_readable_artifact_identity.py
scripts/build_workflow_dispatch_issue_event.py
scripts/check_projects_bundle_readiness.py
scripts/project_copilot_advisory_fields.py
scripts/project_copilot_advisory_from_run.py
scripts/project_copilot_advisory_v2_fields.py
scripts/projects_bundle_manifest_contract.py
scripts/projects_bundle_readiness_contract.py
scripts/reconcile_projectv2_configuration.py
scripts/run_workflow_dispatch_authoritative_request.py
projectv2_views.json
projects_bundle_manifest.json
COPILOT_ADVISORY_PUBLICATION.md
COPILOT_ADVISORY_V2.md
INSTALLATION.md
PROJECTS_BUNDLE_DRIFT_AUDIT.md
PROJECT_BOARD_TEMPLATE.md
RESULT_UPDATE_PRESENTATION_CONTRACT.md
```

`transversal-event.yml` est retiré : une recherche peut déjà référencer
plusieurs groupes, tickets, résultats, dépôts, chemins, pièces jointes et URL.

Le formulaire `specialist-capability-growth.yml` exprime une demande de capacité
liée à un `specialist_ref` stable. Il peut signaler les preuves et contrats encore
manquants, mais il ne peut ni approuver une révision, ni autoriser le Scheduler :
la décision opérateur reste locale.

Le workflow GitHub est installé uniquement dans `newicody/projects`.
Chaque nouvelle Issue créée avec le formulaire `Nouvelle recherche` porte le
préfixe `[Recherche] ` (avec les deux sections obligatoires du formulaire comme
solution de repli) et déclenche automatiquement son propre run Actions :

```text
issues.opened dans newicody/projects
→ qualification par le préfixe [Recherche]
→ demande autoritative propre à l'Issue
→ avis Copilot requis pour ce run initial
→ manifeste corrélé
→ trois artefacts Actions distincts par Issue et par run
→ premier commentaire Copilot publié par newicody/projects
```

Les vues ProjectV2 préparées restent la surface de classement et de suivi. Elles
ne servent pas de condition au webhook initial, car les champs ProjectV2 peuvent
être renseignés après l'événement `issues.opened`.

Le déclenchement manuel `workflow_dispatch` reste disponible pour les reprises,
continuations et traitements explicitement opérés. Dans ce mode manuel, la
variable `AUTODOC_COPILOT_ADVISORY_ENABLED` conserve son rôle.

Le token automatique du job reste en lecture sur les Issues. Seules les étapes
bornées de publication du premier avis reçoivent le secret
`AUTODOC_ISSUE_COMMENT_TOKEN`. Autodoc local récupère ensuite les artefacts sans
republier ce premier commentaire, puis contrôle l'admissibilité avant de remettre
une commande au Scheduler et au laboratoire.

La configuration `projectv2_views.json` décrit les champs et les vues
`Recherches`, `Résultats`, `Copilot`, `Connaissances serveur`,
`Boîtes de thèmes`, `Historique` et `Tous`.

Le serveur local ne crée pas les artefacts initiaux. Il effectue le fetch des
runs produits par `newicody/projects`, vérifie leur corrélation
`repository/issue_number/run_id/digests`, puis déclenche le laboratoire seulement
si la demande est admissible. Le chemin historique
`ProjectV2 query-only → diff local` reste réservé aux transitions et reprises
explicites ; il ne crée pas le triplet initial des nouvelles recherches.

Pour les nouvelles Issues de recherche, l'avis Copilot initial est requis et ne
dépend plus de la variable optionnelle. Pour les seuls dispatchs manuels, cette
variable conserve son rôle :

```text
AUTODOC_COPILOT_ADVISORY_ENABLED=true
```

Aucun secret Copilot durable n'est attendu. Le premier commentaire utilise le
secret borné `AUTODOC_ISSUE_COMMENT_TOKEN`; la création des champs/vues et la
projection ProjectV2 utilisent un PAT classique distinct, uniquement lors
d'une opération explicitement approuvée.


## Manifest géré et audit de dérive

`projects_bundle_manifest.json` définit les chemins actifs et retirés.
`scripts/audit_projects_bundle_drift.py` compare leurs SHA-256 sans mutation.
Le mode opératoire complet est dans `PROJECTS_BUNDLE_DRIFT_AUDIT.md`.
Les caches `__pycache__`, `*.pyc` et `*.pyo` sont signalés séparément dans
`ignored_transient_files`; les autres fichiers inconnus restent soumis à revue.
