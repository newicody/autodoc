# 0224 — Data Surface EventBus Upstream Contract

## Decision

GitHub artifact, SourceCandidate, SQL, Qdrant, rehydration, and pushback surfaces
are observable upstream sources for the passive supervision path.

They must emit or expose canonical events through the EventBus.

The passive supervisor consumes those events downstream and updates its in-memory
cellular projection.

```text
GitHub artifact / SourceCandidate / SQL / Qdrant / Rehydrate / Pushback
  -> EventBus
  -> PassiveSupervisorSink
  -> CellularState
  -> optional snapshot
  -> optional audit/replay
```

The supervisor is not a data orchestrator, not a persistence worker, not a Qdrant
projection worker, not a GitHub client, and not a pushback agent.

## Relation to Scheduler

The Scheduler remains the orchestration authority.

The Scheduler may cause or coordinate data-surface operations through existing
runtime paths, but the supervisor only observes their emitted EventBus events.

The supervisor must never call, wrap, or trigger `Scheduler.run()`.

## Relation to GitHub artifact flow

GitHub artifact events may describe:

```text
artifact_seen
artifact_fetched
artifact_verified
artifact_rejected
artifact_import_requested
artifact_imported
artifact_failed
```

The supervisor may display the artifact lifecycle and carry `artifact_ref`.

The supervisor must not:

```text
call GitHub APIs
fetch artifacts
upload artifacts
mutate issues
mutate projects
post comments
change labels
change status fields
```

## Relation to SourceCandidate

SourceCandidate events may describe:

```text
source_candidate_seen
source_candidate_validated
source_candidate_rejected
source_candidate_promoted
source_candidate_failed
```

The supervisor may display the candidate lifecycle and carry
`source_candidate_ref`.

The supervisor must not validate, promote, reject, or enrich candidates. Those
choices belong to the ingestion/policy/orchestration layers.

## Relation to SQL

SQL events may describe:

```text
sql_write_requested
sql_written
sql_read_requested
sql_read
sql_rehydrate_ref_seen
sql_failed
```

The supervisor may display SQL activity and carry `sql_ref`.

SQL remains durable authority for local records. The supervisor must not write,
read, migrate, or reconcile SQL state.

## Relation to Qdrant

Qdrant events may describe:

```text
qdrant_projection_requested
qdrant_projected
qdrant_recall_requested
qdrant_recalled
qdrant_failed
```

The supervisor may display projection/recall activity and carry `qdrant_ref`.

Qdrant remains a projection/search/recall surface. The supervisor must not write,
query, create collections, delete collections, or reconcile Qdrant state.

## Relation to rehydration

Rehydration events may describe:

```text
rehydration_requested
rehydration_sql_ref_seen
rehydration_context_loaded
rehydration_completed
rehydration_failed
```

The supervisor may display rehydration progress and carry `sql_ref`, `qdrant_ref`,
and `handoff_ref`.

The supervisor must not hydrate context itself.

## Relation to pushback

Pushback events may describe:

```text
pushback_requested
pushback_prepared
pushback_sent
pushback_skipped
pushback_failed
```

The supervisor may display pushback state and carry `pushback_ref`.

The supervisor must not mutate GitHub, send pushback, or decide whether pushback is
allowed.

## Canonical observable refs

Data-surface events should preserve first-level references when available:

```text
artifact_ref
source_candidate_ref
sql_ref
qdrant_ref
handoff_ref
pushback_ref
policy_decision_id
route_ref
```

These references allow the cellular projection to show movement of a datum across
surfaces without making the supervisor authoritative.

## Cellular movement

Cells may be grouped by locality and may appear to move when a datum, route,
lease, artifact, source candidate, SQL reference, Qdrant reference, or pushback
reference is transmitted elsewhere.

This movement is a visualization/projection effect only.

It must not imply that the supervisor owns, transfers, validates, stores, or
controls the underlying object.

## Forbidden paths

The following paths are forbidden for this contract:

```text
EventBus -> events.jsonl -> supervisor as the normal path
status.json -> supervisor as the normal path
supervisor -> GitHub mutation
supervisor -> SQL write/read
supervisor -> Qdrant write/query
supervisor -> SourceCandidate promotion/rejection
supervisor -> rehydration execution
supervisor -> pushback send
supervisor -> Scheduler.run()
supervisor -> proxy control
supervisor -> policy decision
```

`events.jsonl` may exist only as optional audit/replay/debug output.

## Acceptance

This contract is accepted when documentation and rule tests state that data
surfaces are upstream EventBus sources and that the supervisor remains downstream,
read-only, and non-authoritative.
