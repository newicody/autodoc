# 0224 Code Rule — Data Surface EventBus Upstream Contract

Any GitHub artifact, SourceCandidate, SQL, Qdrant, rehydration, or pushback
supervision integration MUST use EventBus as the canonical upstream observation
path and MUST keep the passive supervisor downstream-only.

The passive supervisor MAY:

- accept canonical EventBus events
- update an in-memory cellular projection
- expose snapshots
- optionally write audit/replay records
- preserve first-level refs such as `artifact_ref`, `source_candidate_ref`,
  `sql_ref`, `qdrant_ref`, `handoff_ref`, and `pushback_ref`

The passive supervisor MUST NOT:

- call GitHub APIs
- fetch or upload GitHub artifacts
- mutate GitHub issues, projects, comments, labels, or statuses
- validate, promote, reject, or enrich SourceCandidates
- write, read, migrate, or reconcile SQL state
- write, query, create, delete, or reconcile Qdrant state
- execute rehydration
- send pushback
- call or wrap `Scheduler.run()`
- control RouteProxy or ControlProxy
- mutate SHM
- make policy decisions
- introduce a new EventBus
- make `events.jsonl` or `status.json` the normal runtime path

`events.jsonl` is allowed only as optional audit/replay/debug output.
