# 0287-r7-r15-r3-r16-r2-projects-bundle-managed-manifest-and-drift-audit

This unit adds a versioned ownership manifest and a strictly read-only local
drift audit for the bundle copied into `newicody/projects`.

## Dry-run

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r2-projects-bundle-managed-manifest-and-drift-audit \
  --dry-run \
  --allow-dirty
```

## Commit and push

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r2-projects-bundle-managed-manifest-and-drift-audit \
  --commit \
  --push \
  --allow-dirty
```

## First audit after integration

```bash
AUTODOC=/home/eric/projet/git/autodoc
PROJECTS=/home/eric/projet/git/projects
SRC="$AUTODOC/templates/github/projects-repository"

python "$SRC/scripts/audit_projects_bundle_drift.py" \
  --source "$SRC" \
  --destination "$PROJECTS" \
  --format json |
tee /tmp/projects-bundle-drift.json
```

Do not delete unknown extra files. Only paths listed in
`safe_delete_candidates` are known retired Autodoc-managed files.
