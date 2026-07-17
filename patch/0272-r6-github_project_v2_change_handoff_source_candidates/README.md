# 0272-r6 — GitHub ProjectV2 change handoff SourceCandidates

## Intent

Convert immutable local ProjectV2 change sets from 0272-r4 into bounded,
immutable handoff batches that reuse the existing `SourceCandidate` contract.
The batch remains behind a future operator acceptance gate.

The patch also documents the complete manual GitHub ProjectV2/GitHub Actions
configuration. It deliberately provides no installation or deployment script.

## Dependencies

Apply after:

1. `0272-r4-github_project_v2_snapshot_change_detection`
2. `0272-r5-github_project_system_deployment_readiness`

## Main operator command

```bash
PYTHONPATH=src:. python \
  tools/build_github_project_v2_change_handoffs_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-v2-change-handoff \
  --format summary
```

## Boundaries

- no GitHub call or mutation;
- no installation/deployment script;
- no SQL write;
- no Qdrant projection;
- no Scheduler/SHM modification;
- removed Project items remain advisory;
- no non-stdlib dependency;
- work bounded by `max_handoffs`.

## Validation performed during construction

```text
git apply --check on fresh r5 base: OK
git apply on fresh r5 base: OK
compileall after fresh apply: OK
r4/r5/r6 targeted regressions after fresh apply: 26 passed
runtime and canonical DOT parse after fresh apply: OK
CLI mode after fresh apply: 100755
```

Run the complete repository gates after application:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```
