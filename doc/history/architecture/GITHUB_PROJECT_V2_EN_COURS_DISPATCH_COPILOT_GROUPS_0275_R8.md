# ProjectV2 `En cours` dispatch, Copilot and theme boxes — 0275-r8

## Décision

Le déplacement d'une carte dans `En cours` est l'acte opérateur qui démarre
une exécution. Les colonnes `Recherche`, `Développement` et `Production`
définissent l'intention immédiatement précédente.

## Composition réutilisée

```text
run_github_project_v2_query_only_snapshot_0272.py
→ detect_github_project_v2_snapshot_changes_0272.py
→ github_project_v2_en_cours_dispatch_0275_r8.py
→ dispatch_github_project_v2_en_cours_transitions_0275_r8.py
```

Le nouveau contrat consomme directement `items.changed[].status.before/after`
et `items.changed[].after.content` du change set 0272. Aucun second lecteur
GraphQL ou modèle ProjectV2 n'est ajouté.

## Idempotence

Chaque transition reçoit un identifiant déterministe dérivé de :

```text
change_set_ref
project_item_id
previous_status
current_status
```

L'identifiant n'est enregistré qu'après succès du `workflow_dispatch`.
Le compteur durable par issue choisit `initial` au premier cycle et
`continuation` aux cycles suivants. Les issues `[Événement lié]` utilisent
`transversal`.

## Frontières

La section globale `[safety]` reste query-only et interdit toute mutation.
Une section distincte `[workflow_dispatch]` autorise uniquement l'appel borné
du workflow de `newicody/projects`.

```text
Project mutation = interdite
Issue mutation   = interdite
Workflow dispatch = autorisé et borné
SQL/Qdrant       = interdits
Scheduler        = inchangé
```

## Groupes

Deux représentations complémentaires sont conservées :

- `Group by Thème` : plusieurs bandes visuelles libres ;
- `Group by Parent issue` : une boîte hiérarchique réelle par ticket `[Thème]`.

Le parent principal n'empêche pas de citer plusieurs thèmes dans l'événement
transversal.
