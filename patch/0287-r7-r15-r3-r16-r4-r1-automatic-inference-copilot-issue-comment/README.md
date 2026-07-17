# 0287-r7-r15-r3-r16-r4-r1-automatic-inference-copilot-issue-comment

## Objectif

Rendre automatique la publication du premier avis Copilot pour chaque Issue
qualifiée pour l’inférence par le connecteur ProjectV2 existant.

Le workflow `newicody/projects` conserve ses trois artefacts corrélés et publie
désormais l’avis sous l’Issue sous forme de commentaire Markdown consultatif.
Le corps de l’Issue reste la demande autoritative.

## Réutilisation

Cette unité ne crée aucun nouveau publicateur. Elle compose les surfaces déjà
présentes :

- `build_copilot_advisory_v2_publication_preview.py` ;
- `github_copilot_advisory_v2_issue_publication_0287.py` ;
- `publish_github_copilot_advisory_v2_issue_comment_0287.py`.

Le plan digest, le marqueur idempotent, la détection de collision et le readback
restent ceux de ces composants existants.

## Application Autodoc

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r4-r1-automatic-inference-copilot-issue-comment \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r4-r1-automatic-inference-copilot-issue-comment \
  --commit \
  --push \
  --allow-dirty
```

## Validation ciblée

```bash
PYTHONPATH=src:. /home/eric/python/bin/python -m pytest -q \
  tests/rules/test_automatic_copilot_issue_comment_0287_r16_r4_r1_rule.py
```

Résultat de génération : `4 passed`, YAML valide et `git apply --check` réussi.

## Synchronisation vers newicody/projects

```bash
AUTODOC=/home/eric/projet/git/autodoc
PROJECTS=/home/eric/projet/git/projects
SRC="$AUTODOC/templates/github/projects-repository"

rsync -aiv --exclude README.md "$SRC"/ "$PROJECTS"/
cp "$SRC/README.md" "$PROJECTS/AUTODOC_PROJECTS_BUNDLE.md"

git -C "$PROJECTS" status --short
git -C "$PROJECTS" add .
git -C "$PROJECTS" commit -m "Publish Copilot advisory comments automatically"
git -C "$PROJECTS" push
```

L’audit du bundle doit signaler seulement les fichiers modifiés attendus avant
la copie, puis `managed_exact=true` après synchronisation.

## Configuration de l’automatisation locale

Dans `.var/config/github_projects_workflow_dispatch.ini`, conserver
`target_status = En cours` et ouvrir les deux portes du dispatch local :

```ini
allow_workflow_dispatch = true
allow_remote_mutation = true
```

Le connecteur local doit ensuite exécuter périodiquement :

```bash
export GITHUB_TOKEN="$(gh auth token)"

python tools/dispatch_github_project_v2_en_cours_transitions_0275_r8.py \
  --config .var/config/github_projects_workflow_dispatch.ini \
  --execute \
  --policy-decision-id policy:projects:en-cours-inference-dispatch \
  --format json
```

Chaque nouvelle transition vers `En cours` est idempotente : une décision déjà
dispatchée reste dans le state local et n’est pas relancée.

## Test immédiat sur l’Issue 15

Après le push du dépôt Projects :

```bash
gh variable set AUTODOC_COPILOT_ADVISORY_ENABLED \
  --body true \
  --repo newicody/projects

gh workflow run autodoc-controlled-research.yml \
  --repo newicody/projects \
  --ref master \
  -f issue_number=15 \
  -f requested_status=Recherche \
  -f request_mode=initial \
  -f parent_event_ref=""
```

Le run doit produire les trois artefacts et un commentaire commençant par :

```text
## Autodoc — premier avis Copilot
```

Vérification :

```bash
gh api repos/newicody/projects/issues/15/comments \
  --jq '.[] | select(.body | contains("autodoc:copilot-advisory-v2")) | {html_url, body}'
```

## Frontières

- pas de trigger global `issues:` ;
- la qualification reste la transition ProjectV2 locale vers `En cours` ;
- pas de modification du corps de l’Issue ;
- pas de sous-Issue ;
- pas de Scheduler ni de laboratoire ;
- pas de SQL, Qdrant ou mutation ProjectV2 ;
- le commentaire est consultatif et non autoritatif ;
- les trois uploads utilisent `always()` afin de survivre à un échec de
  publication du commentaire.
