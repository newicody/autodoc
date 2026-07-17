# 0277-r2 — Copilot advisory optional fallback

## Base and purpose

This revision is rebuilt against the exact uploaded working-tree context for
Autodoc commit `9113bb6734eeda79eedf9d0f88ddf148db54458d`.

It fixes the GitHub Actions Copilot advisory path without making Copilot
mandatory or authoritative:

- both versioned workflows use the ephemeral GitHub Actions `GITHUB_TOKEN`;
- both request the scoped `copilot-requests: write` permission;
- the obsolete `secrets.AUTODOC_COPILOT_TOKEN` dependency is removed;
- Copilot CLI command failure, timeout, or invalid JSON is non-blocking by
  default and creates no advisory artifact;
- `AUTODOC_COPILOT_REQUIRED=true` remains available as an explicit diagnostic
  gate;
- a stale `copilot_advisory.json` is removed before each attempt;
- CLI stderr and token values are not copied into artifacts;
- the authoritative request builder rejects a missing/fake Issue envelope and
  no longer invents `Untitled GitHub request` or `No description supplied.`;
- an Issue with a valid title and an empty body remains accepted;
- Scheduler and `Scheduler.run()` are unchanged;
- no non-stdlib dependency is introduced.

## Apply

```bash
cd /home/eric/projet/git/autodoc
unzip -o /mnt/data/0277-r2-copilot-advisory-optional-fallback.zip

python apply_patch_queue.py \
  --patch 0277-r2-copilot-advisory-optional-fallback \
  --dry-run \
  --allow-dirty
```

The current dirty state consists of untracked historical `patch/` directories,
so `--allow-dirty` is expected. Review the patch summary before committing.

If the dry-run succeeds:

```bash
python apply_patch_queue.py \
  --patch 0277-r2-copilot-advisory-optional-fallback \
  --commit \
  --push \
  --allow-dirty
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q \
  templates/github/scripts \
  tests/tools

PYTHONPATH=src:. pytest -q \
  tests/rules/test_github_dual_artifact_actions_workflow_0275_rule.py \
  tests/tools/test_github_copilot_advisory_optional_0277.py

PYTHONPATH=src:. pytest -q tests/rules
```

The patch was checked with `git apply --check` against the uploaded exact file
versions and its focused suite reports `10 passed`.

## Deploy to `newicody/projects`

Push this Autodoc patch first. Then copy the corrected workflow from Autodoc to
the `projects` repository:

```bash
cd /home/eric/projet/git/projects
cp /home/eric/projet/git/autodoc/templates/github/projects-repository/.github/workflows/autodoc-controlled-research.yml \
  .github/workflows/autodoc-controlled-research.yml

git diff --check
git diff -- .github/workflows/autodoc-controlled-research.yml
git add .github/workflows/autodoc-controlled-research.yml
git commit -m "Fix optional Copilot advisory execution"
git push origin master
```

No durable Copilot secret is required by the versioned workflow. Enable the
optional advisory with the repository variable:

```bash
gh variable set AUTODOC_COPILOT_ADVISORY_ENABLED \
  --repo newicody/projects \
  --body true
```
