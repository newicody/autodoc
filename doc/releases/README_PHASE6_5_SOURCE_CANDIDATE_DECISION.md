# Phase 6.5 — SourceCandidate Decision Live Path

Phase 6.5 closes the local operator loop started by SourceCandidate intake and
review.

The new capability lets an operator apply an explicit decision to an existing
SourceCandidate:

```bash
PYTHONPATH=src python -m context.source_candidate_decision_cli \
  --store-file /tmp/source_candidates.json \
  --candidate-id sc-example \
  --action reject \
  --reason "not relevant" \
  --format json
```

The CLI is only an adapter. The durable path remains:

```text
CLI args
-> SourceCandidateDecisionCommand
-> EventType.SOURCE_CANDIDATE_DECISION
-> Scheduler
-> Dispatcher
-> SourceCandidateDecisionHandler
-> SourceCandidateStore JSON real backend
-> SourceCandidateDecisionResult
```

No GitHub API is called. A `promote` or `merge` decision only changes the local
candidate status and records the decision contract. Later phases may project
those local decisions to GitHub, but GitHub is still not authoritative.

## Decisions

Allowed actions remain the existing SourceCandidate decision contract:

```text
inspect, relaunch, reject, archive, promote, merge
```

`merge` may include `--target-context-id`.

## Generated docs

Generate architecture SVGs locally with:

```bash
make -C doc
make -C doc clean
```
