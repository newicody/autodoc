# 0287-r7-r15-r3-r16-r4 — local ready-run Copilot v2 ProjectV2 projection

## Objectif

Relier un `ready_run` déjà récupéré par r16-r3 aux adaptateurs de publication
Copilot v2 déjà présents, afin de rendre l’avis visible dans le champ
ProjectV2 `Avis Copilot`.

Cette unité ne télécharge aucun artefact. Elle résout les trois fichiers dans
le dataset durable `raw`, construit le preview v2, prépare le plan ProjectV2,
puis conserve les portes existantes : décision opérateur, deux variables
d’autorisation, digest exact et readback.

## Application

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r4-local-ready-run-copilot-v2-projectv2-projection \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r4-local-ready-run-copilot-v2-projectv2-projection \
  --commit \
  --push \
  --allow-dirty
```

## Validation ciblée

```bash
PYTHONPATH=src:. /home/eric/python/bin/python -m compileall -q src tests tools

PYTHONPATH=src:. /home/eric/python/bin/python -m pytest -q \
  tests/test_github_actions_ready_run_copilot_v2_projection_0287.py \
  tests/rules/test_github_actions_ready_run_copilot_v2_projection_0287_r16_r4_rule.py
```

## Utilisation — preview

```bash
export AUTODOC_PROJECT_TOKEN="$(gh auth token)"

python tools/run_github_actions_ready_run_copilot_v2_projection_0287.py \
  --scan-report /tmp/github-actions-artifact-ready-runs.json \
  --run-id 29613675117 \
  --dataset-root .var/server_datasets/github_artifacts \
  --projects-scripts-dir templates/github/projects-repository/scripts \
  --project-config /home/eric/projet/git/projects/projectv2_views.json \
  --policy-decision-id policy:projects:copilot-v2-projection:r16-r4 \
  --operator-decision approve \
  --format json | \
tee /tmp/copilot-v2-projectv2-preview.json

PLAN_DIGEST="$(jq -r '.projection.plan_digest' /tmp/copilot-v2-projectv2-preview.json)"
printf 'PLAN_DIGEST=%s\n' "$PLAN_DIGEST"
```

Le preview réalise uniquement la lecture GraphQL d’inventaire nécessaire au
plan. Il ne modifie pas ProjectV2.

## Utilisation — exécution contrôlée

```bash
export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_PROJECT_PROJECTION_ALLOWED=true

python tools/run_github_actions_ready_run_copilot_v2_projection_0287.py \
  --scan-report /tmp/github-actions-artifact-ready-runs.json \
  --run-id 29613675117 \
  --dataset-root .var/server_datasets/github_artifacts \
  --projects-scripts-dir templates/github/projects-repository/scripts \
  --project-config /home/eric/projet/git/projects/projectv2_views.json \
  --policy-decision-id policy:projects:copilot-v2-projection:r16-r4 \
  --operator-decision approve \
  --execute \
  --confirm-plan-digest "$PLAN_DIGEST" \
  --format json | \
tee /tmp/copilot-v2-projectv2-execute.json

jq '{
  valid: .projection.valid,
  mutation_performed: .projection.mutation_performed,
  readback_verified: .projection.readback_verified,
  mutations: .projection.mutations,
  issues: .projection.issues
}' /tmp/copilot-v2-projectv2-execute.json
```

Résultat cible :

```text
valid=true
mutation_performed=true
readback_verified=true
```

La projection v2 écrit le résumé humain dans `Avis Copilot` et ne modifie ni
`Route Copilot` ni `Confiance Copilot`, car ces données n’existent pas dans le
schéma v2.
