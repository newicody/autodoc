# 0272-r7 — ProjectV2 SourceCandidate operator gate

## Intent

Correct the GitHub operating model and close the local operator gate:

- ProjectV2 query-only is the primary, project-native path;
- a repository-Issue GitHub Actions workflow is an optional bridge, not a
  prerequisite or installation step;
- one immutable r6 `SourceCandidate` handoff receives one explicit existing
  `SourceCandidateDecision`;
- only `promote` and `merge` authorize a future durable consumer;
- r7 itself performs no SQL/Qdrant write or GitHub mutation.

## Dependencies

Apply after:

1. `0272-r4-github_project_v2_snapshot_change_detection`
2. `0272-r5-github_project_system_deployment_readiness`
3. `0272-r6-github_project_v2_change_handoff_source_candidates`

## Project-native readiness

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-native-readiness \
  --format summary
```

The optional repository-Issue Actions bridge is verified only when requested:

```bash
PYTHONPATH=src:. python \
  tools/run_github_project_system_deployment_readiness_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --check-actions-bridge \
  --policy-decision-id policy:0272:actions-bridge-readiness \
  --format summary
```

## Operator gate

```bash
PYTHONPATH=src:. python \
  tools/gate_github_project_v2_source_candidate_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --candidate-id ghpv2-... \
  --action promote \
  --reason "accepted by operator" \
  --execute \
  --policy-decision-id policy:0272:source-candidate-gate \
  --format summary
```

Allowed actions: `inspect`, `relaunch`, `reject`, `archive`, `promote`, `merge`.
`merge` requires `--target-context-id`. Removed ProjectV2 items are advisory and
cannot be promoted or merged.

## Boundaries

- no installation or deployment script;
- no automatic workflow copy, commit, push or dispatch;
- no GitHub call in the gate;
- no GitHub mutation anywhere in r7;
- no SQL write or Qdrant projection;
- no Scheduler/SHM modification;
- no non-stdlib dependency.

## Construction validation

```text
git diff --check: OK
compileall synthetic r4/r5/r6/r7 workspace: OK
complete synthetic r4/r5/r6/r7 suite: 38 passed
runtime and canonical DOT parse: OK
```

Run the complete repository gates after application:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```
