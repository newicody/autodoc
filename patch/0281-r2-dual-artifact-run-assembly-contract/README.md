# 0281-r2-dual-artifact-run-assembly-contract

## Purpose

Add the pure run-level assembly contract between already-downloaded GitHub
Actions artifacts and the existing 0275 dual-artifact intake.

## Repository impact

```text
newicody/autodoc: modification required
newicody/projects: no modification required
```

The workflow in `projects` already emits the expected request, advisory and
manifest names. This patch does not change GitHub Actions.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0281-r2-dual-artifact-run-assembly-contract \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0281-r2-dual-artifact-run-assembly-contract \
  --commit \
  --push \
  --allow-dirty
```

## Targeted tests

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_dual_artifact_run_assembly_0281.py \
  tests/rules/test_github_dual_artifact_run_assembly_0281_rule.py
```
