# Publication contrôlée des avis Copilot

Le workflow produit trois artefacts :

```text
autodoc-authoritative-request
autodoc-copilot-advisory
autodoc-dual-artifact-manifest
```

Il ne remplit volontairement aucun champ ProjectV2. La publication locale
vérifie les trois artefacts, construit le preview puis réutilise
`project_copilot_advisory_fields.py`.

## Prérequis

```bash
cd /home/eric/projet/git/projects

gh variable get AUTODOC_COPILOT_ADVISORY_ENABLED \
  --repo newicody/projects

export AUTODOC_PROJECT_TOKEN="$(gh auth token -h github.com)"
```

La variable GitHub doit valoir `true`. Le token local doit avoir le scope
`project`.

Lister les exécutions :

```bash
gh run list \
  --repo newicody/projects \
  --workflow autodoc-controlled-research.yml \
  --limit 10
```

## Preview

```bash
RUN_ID='<run-id>'
ISSUE_NUMBER='<issue-number>'
POLICY_DECISION_ID='policy:copilot-advisory-publication:<id>'

python scripts/project_copilot_advisory_from_run.py \
  --run-id "$RUN_ID" \
  --repository newicody/projects \
  --issue-number "$ISSUE_NUMBER" \
  --policy-decision-id "$POLICY_DECISION_ID" \
  --operator-decision approve \
  --format json |
tee /tmp/copilot-projectv2-plan.json
```

Le preview télécharge et corrèle les artefacts, puis affiche le
`plan_digest`. Il ne réalise aucune mutation.

## Exécution après revue

```bash
PLAN_DIGEST="$(
  jq -r '.projection.plan_digest' \
    /tmp/copilot-projectv2-plan.json
)"

export AUTODOC_REMOTE_MUTATION_ALLOWED=true
export AUTODOC_PROJECT_PROJECTION_ALLOWED=true

python scripts/project_copilot_advisory_from_run.py \
  --run-id "$RUN_ID" \
  --repository newicody/projects \
  --issue-number "$ISSUE_NUMBER" \
  --policy-decision-id "$POLICY_DECISION_ID" \
  --operator-decision approve \
  --execute \
  --confirm-plan-digest "$PLAN_DIGEST" \
  --format json
```

Les champs projetés sont ceux définis dans `projectv2_views.json`, notamment :

```text
Copilot
Avis Copilot
Route Copilot
Confiance Copilot
Dernière mise à jour
Artefact
Cycle
```

## Relecture

Relancer l’outil de lecture/query-only ou ouvrir la vue `Copilot`. Le statut
doit correspondre à l’option configurée, et les champs doivent contenir le
résumé, la route, la confiance et les références des artefacts.

## Limites d’autorité

```text
requête autoritative        = true
avis Copilot autoritatif    = false
décision opérateur requise  = true
confirmation digest requise = true
workflow auto-publicateur   = false
```
