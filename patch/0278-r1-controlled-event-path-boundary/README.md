# 0278-r1 — Controlled GitHub event path boundary

## Purpose

GitHub Actions reserves the `GITHUB_*` environment namespace. The controlled
`workflow_dispatch` workflow attempted to replace `GITHUB_EVENT_PATH` with a
synthetic Issue event, but the runner retained the native dispatch payload.
That payload has no top-level `issue` object, so the authoritative request
builder rejected it.

This patch:

- passes the normalized synthetic event through `AUTODOC_EVENT_PATH`;
- makes the authoritative request builder prefer `AUTODOC_EVENT_PATH`;
- keeps `GITHUB_EVENT_PATH` as the fallback for native GitHub Issue events;
- adds a regression test where both paths exist and the controlled path wins;
- modifies neither Scheduler nor `Scheduler.run()`;
- adds no non-stdlib dependency and no remote mutation.

## Prerequisite

Apply after `0277-r2-copilot-advisory-optional-fallback`.

## Apply

```bash
cd /home/eric/projet/git/autodoc
unzip -o /mnt/data/0278-r1-controlled-event-path-boundary.zip

python apply_patch_queue.py \
  --patch 0278-r1-controlled-event-path-boundary \
  --dry-run \
  --allow-dirty
```

If the dry-run succeeds:

```bash
python apply_patch_queue.py \
  --patch 0278-r1-controlled-event-path-boundary \
  --commit \
  --push \
  --allow-dirty
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q templates/github/scripts tests/tools

PYTHONPATH=src:. pytest -q \
  tests/rules/test_github_dual_artifact_actions_workflow_0275_rule.py \
  tests/tools/test_github_copilot_advisory_optional_0277.py
```

Focused result during construction: `11 passed`.

## Deploy to `newicody/projects`

Push Autodoc first, then synchronize the workflow:

```bash
cd /home/eric/projet/git/projects
cp /home/eric/projet/git/autodoc/templates/github/projects-repository/.github/workflows/autodoc-controlled-research.yml \
  .github/workflows/autodoc-controlled-research.yml

git diff --check
git diff -- .github/workflows/autodoc-controlled-research.yml
git add .github/workflows/autodoc-controlled-research.yml
git commit -m "Fix controlled Issue event path"
git push origin master
```
