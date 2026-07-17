# 0272-r3 — GitHub ProjectV2 query-only snapshot

## Base

```text
8971877361bf7d1d1b127700304088791de57b78
r2-github-actions-artifact-scan-once-live-binding
```

## Purpose

Realign the canonical GitHub workflow source to the real user ProjectV2
`newicody / project 2` while keeping the 0272-r2 GitHub Actions artifact path as
a secondary optional exchange surface.

The patch adds one bounded GraphQL query-only scan that writes a deterministic,
content-addressed local snapshot.  It rejects GraphQL mutation operations,
requires an explicit decision for live execution, reads the token only from
`GITHUB_TOKEN`, and performs no remote mutation, SQL write, Qdrant write,
Scheduler change or SHM operation.

## Reuse decision

`github_project_push_frame_config` is reused for the validated Project owner,
number, token environment variable and fcron-compatible configuration.  The
repository contains no reusable ProjectV2 GraphQL query client, which justifies
the narrow stdlib IO boundary added by this patch.  No non-stdlib dependency is
added.

## Apply

```bash
tar -xJf /mnt/data/0272-r3-github_project_v2_query_only_snapshot.tar.xz
python apply_patch_queue.py \
  --patch 0272-r3-github_project_v2_query_only_snapshot \
  --dry-run \
  --allow-dirty
python apply_patch_queue.py \
  --patch 0272-r3-github_project_v2_query_only_snapshot \
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

## Plan-only smoke

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_v2_query_only_snapshot_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --output .var/reports/github_project_v2_query_only_snapshot_0272.json \
  --format summary
```

## Live query-only smoke

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_v2_query_only_snapshot_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-v2-query-only \
  --output .var/reports/github_project_v2_query_only_snapshot_0272.json \
  --format summary
```
