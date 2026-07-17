# 0269-r1-production_prototype_smoke_composition

## Objet

Ajoute une surface opérateur one-shot qui compose strictement les outils existants :

```text
0260 -> 0261 -> 0262 -> 0263 -> 0264 -> 0265 -> 0266 -> 0267 -> 0268
```

0269 ne réimplémente aucune phase et n'introduit ni `RuntimeManager`, ni service manager, ni nouvelle autorité métier. Le cœur typé construit un plan déterministe et agrège des résultats immuables ; seule la CLI exécute les outils Python déjà présents.

## Audit de réutilisation

Le dépôt contient déjà `tools/run_p1_closed_loop_operator_smoke.py`, mais cette surface compose l'ancien chemin 0145/0148/0151 avec un contrat différent. Elle n'est pas un hôte compatible pour 0260-0268.

0269 réutilise directement :

- `bind_scheduler_managed_db_api_sql_context_store_0260.py` ;
- `run_scheduler_managed_sql_ref_openvino_embedding_0261.py` ;
- `run_scheduler_managed_embedding_qdrant_projection_0262.py` ;
- `run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py` ;
- `compose_scheduler_managed_closed_result_frame_0264.py` ;
- `build_closed_result_frame_eventbus_observation_0265.py` ;
- `build_passive_supervisor_closed_result_frame_observation_0266.py` ;
- `build_github_scan_once_handoff_0267.py` ;
- `build_openrc_launcher_minimal_readiness_0268.py`.

## Modes et gates

Le mode par défaut est un plan sans effet.

Le mode `--execute` exige :

- un `--policy-decision-id` explicite ;
- `--demo-qdrant`, car 0262/0263 n'exposent actuellement que les exécuteurs Qdrant de démonstration injectés ;
- OpenVINO/E5 réel par défaut ; `--demo-embedding` reste un choix explicite de test ;
- la publication sur l'EventBus en mémoire reste optionnelle et explicite via `--demo-eventbus`.

Le rapport final n'est valide que si les neuf rapports sont valides, si les références `sql_ref`, `embedding_ref`, `handoff_ref` et `readiness_ref` sont présentes, et si les frontières observation-only, SQLite présente, absence de mutation GitHub et absence de démarrage de services sont confirmées.

## Frontières verrouillées

- aucun démarrage PostgreSQL, Qdrant ou OpenVINO ;
- aucun appel `rc-service` ou `rc-update` ;
- OpenRC/OS/admin reste l'autorité des processus externes ;
- aucune API GitHub et aucune mutation distante ;
- EventBus reste observation-only ;
- PassiveSupervisor reste lecture passive ;
- SQL reste l'autorité durable ;
- Qdrant reste projection/recall avec `payload.sql_ref` ;
- aucune modification de `Scheduler.run()` ;
- aucune dépendance hors bibliothèque standard ajoutée.

## Base exacte

```text
repository: newicody/autodoc
branch: master
base_commit: 758312df52ad04c9fee6651978dd54274e9d528a
```

Les nouveaux chemins de code 0269 sont absents de ce commit public. La rustine est add-only.

## Application

```bash
git status --short
git log --oneline -5
git diff

tar -xJf /mnt/data/0269-r1-production_prototype_smoke_composition.tar.xz

python apply_patch_queue.py \
  --patch 0269-r1-production_prototype_smoke_composition \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0269-r1-production_prototype_smoke_composition \
  --commit \
  --push \
  --allow-dirty
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

Validation ciblée effectuée pendant la construction :

```text
10 passed
```

## Plan 0269

```bash
PYTHONPATH=src:. python \
  tools/run_production_prototype_smoke_composition_0269.py \
  --output .var/reports/production_prototype_smoke_composition_0269.json \
  --format summary
```

## Smoke complet 0269

```bash
PYTHONPATH=src:. python \
  tools/run_production_prototype_smoke_composition_0269.py \
  --execute \
  --policy-decision-id policy:0269:operator \
  --demo-eventbus \
  --demo-qdrant \
  --output .var/reports/production_prototype_smoke_composition_0269.json \
  --format summary
```

Ajouter `--model-dir <chemin>` si le modèle OpenVINO/E5 n'est pas résolu par la configuration existante. `--demo-embedding` est réservé au test déterministe explicite.

Sortie attendue :

```text
production_prototype_smoke_composition_valid=True issues=0 execute=True steps=9/9 sql_ref=sql:... embedding_ref=embedding:... handoff_ref=github-scan-once-handoff:... readiness_ref=openrc-launcher-readiness:... remote_mutation_allowed=False services_started=False
```
