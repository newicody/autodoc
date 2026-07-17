# 0272-r5 — GitHub Project system deployment readiness

## Required base

Apply `0272-r4-github_project_v2_snapshot_change_detection` first.  The public
base audited for existing preimages is `dd5cd46db4a5236558d82539c98b1d74ce1b2b05`
(0272-r3); r4 adds only new files and does not modify the README, shared config
or canonical global graph changed by this patch.

## Purpose

Add one Python readiness command, driven by the existing 0272 `.ini`, that tests
an already-installed local ProjectV2 path and an already-deployed secondary
GitHub Actions workflow.  It never installs, copies, commits, pushes, deploys,
dispatches or mutates anything.

## Read-only checks

- local config, r3 snapshot tool, r4 change detector and workflow templates;
- workflow policy: issue trigger, upload-artifact v4, no workflow_dispatch,
  no write permission and no mutation command;
- ProjectV2 identity through a GraphQL query operation only;
- workflow metadata and deployed workflow/builder contents through REST GET;
- SHA-256 equality between local templates and deployed files;
- active workflow state and configured path.

## Apply

```bash
tar -xJf /mnt/data/0272-r5-github_project_system_deployment_readiness.tar.xz
python apply_patch_queue.py \
  --patch 0272-r5-github_project_system_deployment_readiness \
  --dry-run \
  --allow-dirty
python apply_patch_queue.py \
  --patch 0272-r5-github_project_system_deployment_readiness \
  --commit \
  --push \
  --allow-dirty
```

## Validate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Local readiness

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --format summary
```

## Live query-only readiness

```bash
export GITHUB_TOKEN='...'

PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:deployment-readiness \
  --format summary
```

The example still targets the secondary repository
`newicody/autodoc-ideas`.  Until that repository exists and the two existing
templates are manually copied to their configured destinations, the live
readiness report is expected to expose the missing deployment rather than hide
or repair it.
