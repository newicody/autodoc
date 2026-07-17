# 0287-r7-r15-r3-r16-r2-r2-projects-bundle-transient-python-ignore

This patch follows the first real local Projects bundle drift audit. It keeps
Python bytecode visible under `ignored_transient_files` instead of treating it
as repository drift.

## Dry-run

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r2-r2-projects-bundle-transient-python-ignore \
  --dry-run \
  --allow-dirty
```

## Commit and push

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r2-r2-projects-bundle-transient-python-ignore \
  --commit \
  --push \
  --allow-dirty
```

After synchronizing the updated bundle into `newicody/projects`, rerun:

```bash
python templates/github/projects-repository/scripts/audit_projects_bundle_drift.py \
  --source templates/github/projects-repository \
  --destination /home/eric/projet/git/projects \
  --format json
```
