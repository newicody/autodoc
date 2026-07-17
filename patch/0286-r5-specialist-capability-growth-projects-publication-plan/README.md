# 0286-r5 — Specialist capability-growth Projects publication plan

Ce patch ajoute un contrat pur et immuable qui transforme la projection de
revue 0286-r2 en un plan unique de publication GitHub Projects.

Le plan regroupe :

- un commentaire Issue append-only avec marqueur d'idempotence ;
- les neuf valeurs ProjectV2 installées en 0286-r4 ;
- la détection create/replay/collision du commentaire ;
- les actions set/replay des champs ;
- un `plan_digest` SHA-256 couvrant l'ensemble du plan.

Une collision de commentaire bloque également les écritures ProjectV2. Le
patch ne contacte pas GitHub et ne réalise aucune mutation distante.

## Prérequis

Les patchs 0286-r2, 0286-r3, 0286-r4 et leurs correctifs cumulatifs doivent être
présents dans l'arbre.

## Application

```bash
python apply_patch_queue.py \
  --patch 0286-r5-specialist-capability-growth-projects-publication-plan \
  --commit \
  --push \
  --allow-dirty
```

## Validation ciblée

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_specialist_capability_growth_projects_review_projection_0286.py \
  tests/context/test_specialist_capability_growth_projects_publication_plan_0286.py \
  tests/rules/test_specialist_capability_growth_projects_publication_plan_0286_rule.py
```

Résultat de construction : `32 passed`.

La suite globale `tests/rules` est exécutée automatiquement par
`apply_patch_queue.py`.
