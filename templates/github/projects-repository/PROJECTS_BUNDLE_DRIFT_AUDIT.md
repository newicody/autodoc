# Audit de dérive du bundle `newicody/projects`

Ce runbook complète `INSTALLATION.md` sans augmenter son budget verrouillé. Il
compare localement le bundle Autodoc avec le checkout de `newicody/projects`.
Il n'effectue aucune mutation et n'accède pas au réseau.

## Préparer les chemins

```bash
AUTODOC=/home/eric/projet/git/autodoc
PROJECTS=/home/eric/projet/git/projects
SRC="$AUTODOC/templates/github/projects-repository"
DST="$PROJECTS"
MANIFEST="$SRC/projects_bundle_manifest.json"
```

## Auditer avant la copie

```bash
python "$SRC/scripts/audit_projects_bundle_drift.py" \
  --source "$SRC" \
  --destination "$DST" \
  --manifest "$MANIFEST" \
  --format json |
tee /tmp/projects-bundle-drift-before.json
```

```bash
jq '{
  bundle_ref,
  bundle_version,
  source_valid,
  managed_exact,
  review_required,
  copy_candidates,
  safe_delete_candidates,
  unknown_extra_files,
  ignored_transient_files,
  plan_digest,
  boundaries
}' /tmp/projects-bundle-drift-before.json
```

## Interpréter le résultat

- `copy_candidates` contient les fichiers gérés absents ou différents ;
- `safe_delete_candidates` contient uniquement les chemins explicitement
  marqués `retired` dans le manifest ;
- `unknown_extra_files` contient des fichiers à examiner, jamais des candidats
  automatiques à la suppression ;
- `ignored_transient_files` contient uniquement les caches Python
  `__pycache__`, `*.pyc` et `*.pyo`; ils ne déclenchent aucune revue ;
- `source_missing` indique une incohérence du bundle Autodoc ;
- `modified` exige une revue avant écrasement ;
- `identical` confirme un SHA-256 source/destination identique.

L'audit reste read-only :

```text
mutation_performed = false
remote_access_performed = false
safe_delete_scope = retired_entries-only
rsync_delete_allowed = false
```

## Copier sans suppression globale

```bash
rsync -aivn --exclude README.md "$SRC"/ "$DST"/
rsync -aiv --exclude README.md "$SRC"/ "$DST"/
cp "$SRC/README.md" "$DST/AUTODOC_PROJECTS_BUNDLE.md"
```

Ne jamais employer `rsync --delete`.

## Traiter les chemins retirés

Ne supprimer un fichier que s'il figure dans `safe_delete_candidates`, après
revue opérateur. Le seul chemin actuellement classé `retired` est :

```bash
rm -f "$DST/.github/ISSUE_TEMPLATE/transversal-event.yml"
```

Ne jamais supprimer automatiquement les chemins de `unknown_extra_files`.

## Relancer l'audit

```bash
python "$SRC/scripts/audit_projects_bundle_drift.py" \
  --source "$SRC" \
  --destination "$DST" \
  --manifest "$MANIFEST" \
  --format json |
tee /tmp/projects-bundle-drift-after.json
```

Le résultat cible est :

```text
source_valid = true
managed_exact = true
copy_candidates = []
safe_delete_candidates = []
```

`ignored_transient_files` peut rester non vide après l'exécution de scripts
Python. `unknown_extra_files` doit rester réservé aux vrais fichiers à revoir.

## Contrôler et publier

```bash
git -C "$DST" status --short
git -C "$DST" diff -- \
  .github scripts projectv2_views.json projects_bundle_manifest.json \
  INSTALLATION.md PROJECTS_BUNDLE_DRIFT_AUDIT.md \
  PROJECT_BOARD_TEMPLATE.md AUTODOC_PROJECTS_BUNDLE.md

git -C "$DST" add .
git -C "$DST" commit -m "Install/update Autodoc Projects bundle"
git -C "$DST" push
```
