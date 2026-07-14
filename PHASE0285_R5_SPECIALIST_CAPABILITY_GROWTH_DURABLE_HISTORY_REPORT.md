# Phase 0285-r5 test report

## Scope

Append-only durable-history port for approved portable-specialist capability revisions.

## Delivered

- immutable append command, entry, snapshot and result contracts;
- SQL-authority history port;
- deterministic test-only in-memory adapter;
- optimistic concurrency, collision rejection and idempotency;
- complete decision/revision/lineage correlation;
- architecture documentation, DOT graph, manifest and changelog;
- systematic review of the cumulative `newicody/projects` installation guide.

## Boundaries

- no real SQL adapter or SQL write;
- no Qdrant write;
- no Scheduler selection or dispatch;
- no laboratory execution;
- no EventBus publication;
- no GitHub or ProjectV2 mutation;
- no update to `INSTALLATION.md`, because the Projects deployment surface is unchanged.

## Validation

Validation performed:

- new r5 context and architecture-rule tests: `18 passed`;
- cumulative targeted r2+r3+r4+r5 chain: `70 passed`;
- `compileall`: passed;
- `git diff --check`: passed;
- `git apply --check` on an isolated compatible base: passed.
