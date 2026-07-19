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


## Exécution opérationnelle r16-r20

Le lanceur complet est :

```text
tools/run_github_research_love_closed_loop_0287.py
```

### Fabriques requises

Le runtime réel est injecté sans être recréé par le lanceur :

```text
--runtime-factory module:function
--reference-point-reader-factory module:function
```

La fabrique principale doit respecter `ImportedActionsRuntimeFactory`. La
seconde retourne le lecteur de point de référence lié à la même collection.

### Préparer le cycle

```bash
python tools/run_github_research_love_closed_loop_0287.py prepare \
  --fetch-cycle-report /tmp/autodoc-fetch-cycle.json \
  --run-id 29622831972 \
  --runtime-factory '<MODULE>:<FACTORY>' \
  --reference-point-reader-factory '<MODULE>:<READER_FACTORY>' \
  --runtime-config .var/config/love_installed_runtime.ini \
  --project-item-id '<PROJECT_ITEM_ID>' \
  --project-field-ref '<RESUME_FIELD_ID>' \
  --project-field-name 'Résumé' \
  --output /tmp/github-love-prepared.json \
  --format summary
```

Le résultat doit indiquer :

```text
valid=true
status=publication-confirmation-required
plan_digest=sha256:...
```

### Contrôler le livrable local

Avant toute mutation, inspecter :

```bash
jq '.prepared.stages.liaison_synthesis' \
  /tmp/github-love-prepared.json

jq '.prepared.stages.final_deliverable_sql' \
  /tmp/github-love-prepared.json

jq '.prepared.stages.publication_plan' \
  /tmp/github-love-prepared.json
```

### Publier et fermer

```bash
PLAN_DIGEST="$(
  jq -r '.publication_plan_digest' \
    /tmp/github-love-prepared.json
)"

export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_ISSUE_PUBLICATION_ALLOWED=true
export AUTODOC_PROJECT_PROJECTION_ALLOWED=true

python tools/run_github_research_love_closed_loop_0287.py complete \
  --prepared-report /tmp/github-love-prepared.json \
  --confirm-plan-digest "$PLAN_DIGEST" \
  --runtime-factory '<MODULE>:<FACTORY>' \
  --runtime-config .var/config/love_installed_runtime.ini \
  --output /tmp/github-love-completed.json \
  --format summary
```

La réussite finale doit produire :

```text
valid=true
status=closed
cycle_closed=true
```

La commande `complete` ne recalcule pas les analyses locales.


### Câblage tool-bounded r16-r20-r1

La fabrique opérationnelle du lanceur est :

```text
context.love_installed_runtime_factory_0287:build_runtime
```

La préparation exige désormais :

```text
--policy-decision-id policy:...
```

Le lecteur de relecture Qdrant est fourni par le port de projection existant;
`--reference-point-reader-factory` n’est plus utilisé.

Pour le provider autonome tool-bounded :

```bash
export AUTODOC_QDRANT_POINT_WRITE_ALLOWED=true
export AUTODOC_QDRANT_SEARCH_ALLOWED=true
```

Le fichier `.var/config/love_installed_runtime.ini` doit contenir :

```ini
[provider]
factory = context.love_tool_bounded_installed_runtime_composer_0287:build_tool_bounded_installed_runtime

[scheduler]
lifecycle = tool-bounded
```


## Configuration dédiée au scan Actions — r16-r20-r2

Ne pas modifier `github_project_v2_query_only.ini` pour le fetch d’artefacts.
Générer une configuration distincte :

```bash
python tools/build_github_actions_artifact_scan_config_0287.py \
  --project-config .var/config/github_project_v2_query_only.ini \
  --fetch-config .var/config/github_artifact_server_fetch.ini \
  --output .var/config/github_actions_artifact_scan.ini \
  --working-directory /home/eric/projet/git/autodoc \
  --python-executable /home/eric/python/bin/python \
  --execute \
  --format summary
```

Vérifier :

```bash
grep -n '^scan_command' \
  .var/config/github_actions_artifact_scan.ini
```

La valeur doit être :

```text
tools/run_github_actions_artifact_scan_once_live_0272.py
```

Le fetch utilise ensuite :

```bash
python tools/run_github_actions_artifact_fetch_once_0287.py \
  --project-config .var/config/github_actions_artifact_scan.ini \
  --fetch-config .var/config/github_artifact_server_fetch.ini \
  --policy-decision-id policy:0287:issue-15-artifact-fetch \
  --max-runs 50 \
  --max-artifacts 150 \
  --execute \
  --format json
```

## Remise locale au Scheduler canonique — r16-r24

### Transition r16-r24-r1 — commande Scheduler typée

La remise GitHub spécifique dans `scheduler.route_requests.jsonl` introduite en
r16-r24 n’est plus le chemin canonique. Elle reste présente uniquement pour la
compatibilité historique et sa CLI refuse désormais l’exécution par défaut.

Ne plus lancer sur le chemin serveur réel :

```text
tools/queue_authorized_github_research_scheduler_intake_0287.py
```

L’ancienne remise ne peut être utilisée qu’avec
`--allow-legacy-filesystem-handoff`, exclusivement pour un test de compatibilité.

Construire d’abord la commande métier typée, sans écriture disque ni SQL, avec
un budget explicite :

```bash
python tools/build_typed_github_research_scheduler_command_0287.py \
  --input /tmp/autodoc-i54-run-29673341210-scheduler-intake.json \
  --max-scheduler-steps 16 \
  --max-specialist-visits 2 \
  --max-wall-time-s 1800 \
  --format summary
```

La sortie attendue contient :

```text
valid=true
status=typed-command-ready-for-sql
legacy_filesystem_handoff_is_canonical=false
sql_write_performed=false
```

Le rapport JSON d’entrée est seulement une projection de frontière provenant du
fetch GitHub. Dans Autodoc, la demande devient une
`GitHubResearchSchedulerCommand`, sous-classe de
`AuthorizedSchedulerCommand`, elle-même sous-classe de `SchedulerCommand`.
L’autorisation, la corrélation, les références de recherche, le budget et la
route sont des objets composés et validés.

Le `command_ref` est stable pour un même intake et un même budget : son identité
utilise l’horodatage déjà présent dans la demande de route autorisée, pas l’heure
de relance de la CLI.

L’unité suivante implémentera le port
`GitHubResearchSchedulerCommandStore` sur PostgreSQL, avec unicité et rejeu
idempotent. Le Scheduler canonique réclamera ensuite la commande SQL ; aucune
file JSONL GitHub spécifique ne sera consommée.

### Persistance PostgreSQL relationnelle — r16-r25

La commande typée est maintenant persistée par le binding PostgreSQL installé.
La connexion existante est réutilisée : aucun runtime complet, Scheduler,
Dispatcher, EventBus, laboratoire, OpenVINO ou Qdrant n'est démarré.

Le stockage interne est relationnel. Aucune commande n'est stockée comme JSON ou
JSONL. Le fichier JSON fourni à la CLI reste uniquement le rapport de frontière
issu du fetch GitHub.

Vérifier sans écrire :

```bash
python tools/persist_typed_github_research_scheduler_command_0287.py \
  --input /tmp/autodoc-i54-run-29673341210-scheduler-intake.json \
  --runtime-config .var/config/love_installed_runtime.ini \
  --max-scheduler-steps 16 \
  --max-specialist-visits 2 \
  --max-wall-time-s 1800 \
  --format summary
```

Résultat attendu :

```text
valid=true mode=dry-run status=typed-command-ready-for-sql
```

Persister réellement dans PostgreSQL :

```bash
python tools/persist_typed_github_research_scheduler_command_0287.py \
  --input /tmp/autodoc-i54-run-29673341210-scheduler-intake.json \
  --runtime-config .var/config/love_installed_runtime.ini \
  --max-scheduler-steps 16 \
  --max-specialist-visits 2 \
  --max-wall-time-s 1800 \
  --execute \
  --format summary
```

Premier passage :

```text
status=scheduler-command-persisted inserted=true state=pending
```

Rejeu identique :

```text
status=scheduler-command-already-persisted idempotent_replay=true state=pending
```

Cette unité s'arrête à `pending`. La réclamation atomique et la remise au
Scheduler local canonique appartiennent à r16-r26.
