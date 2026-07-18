# Installation cumulative — `newicody/projects`

## Publication du livrable final

Le plan r16-r17 est compatible avec l’adaptateur existant
`tools/publish_love_final_deliverable_0287.py`.

### Variables de sécurité

```bash
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_ISSUE_PUBLICATION_ALLOWED=true
export AUTODOC_PROJECT_PROJECTION_ALLOWED=true
```

Le jeton est lu par défaut dans :

```text
AUTODOC_PROJECT_TOKEN
```

Il doit permettre :

- la lecture et la création de commentaires sur l’Issue;
- la lecture du ProjectV2;
- `updateProjectV2ItemFieldValue` sur le champ ciblé.

### Prévisualisation obligatoire

```bash
python tools/publish_love_final_deliverable_0287.py \
  --plan /tmp/r16-r17-publication-plan.json \
  --operator-decision approve \
  --format json
```

Relever `plan_digest`, puis seulement ensuite exécuter :

```bash
python tools/publish_love_final_deliverable_0287.py \
  --plan /tmp/r16-r17-publication-plan.json \
  --operator-decision approve \
  --execute \
  --confirm-plan-digest '<PLAN_DIGEST_EXACT>' \
  --format json
```

La publication est valide uniquement si le commentaire Issue et la valeur du
champ ProjectV2 sont relus exactement.


## Composition complète r16-r19

La composition applicative complète est disponible dans :

```text
context.github_research_love_complete_closed_loop_0287
```

Elle fonctionne en deux appels obligatoires :

1. `prepare_github_research_love_closed_loop` exécute la chaîne locale et
   retourne `publication_plan_digest`;
2. `complete_github_research_love_closed_loop` reçoit ce digest exact, les trois
   autorisations de mutation et les ports Issue/ProjectV2, puis ferme le cycle.

Le processus local doit déjà avoir construit les `ImportedActionsRuntimePorts`
et le Scheduler doit déjà être en cours d’exécution. La composition ne démarre
aucun service.

Les identifiants ProjectV2 à fournir sont :

```text
project_item_id
project_field_ref
project_field_name
```

La fermeture réussie produit une révision SQL dont les métadonnées contiennent :

```text
cycle_status=closed
closure_reason=final-publication-readback-verified
```
