# Current architecture state — canonical index refreshed by 0282-r4

This path remains the canonical high-level current-state index. The filename is
kept for compatibility with earlier documentation links; revision 0282-r4 now
supersedes the 0270 snapshot without deleting historical phase docs.

Compatibility anchor retained for stable rules and links: **canonical index refreshed by 0270**. The phrase identifies the preserved 0270 baseline; it does not override the current 0282-r4 state above.

## Current integrated axes — 0282-r4

```text
0260..0269  SQL durable -> E5 -> Qdrant -> recall -> closed result -> observation
0272..0281  ProjectV2/Issue -> Actions artifacts -> dataset -> fake laboratory -> preview
0282-r1..r4 audit -> lineage -> parent/theme normalization -> append-only history
```

The real GitHub artifact fetch, run-group intake and local closed-loop smoke are
validated. GitHub mutation remains disabled by default. The active ProjectV2
work is now local cycle history: `append`, identical `replay`, or deterministic
`collision`, with no remote effect.

Canonical diagrams:

- `doc/architecture/GLOBAL_ARCHITECTURE_CURRENT_0282.md`;
- `doc/architecture/PROJECTV2_CYCLE_HISTORY_DEVELOPMENT_0282.md`;
- `doc/architecture/PROJECT_BEGINNING_CURRENT_COMPARISON_0282.md`;
- `doc/docs/architecture/runtime/174_rebuilt_runtime_global_current_state.dot`.

## Authority and boundary model

| Role | Current surface | Responsibility | Must not become |
| --- | --- | --- | --- |
| Scheduler orchestration authority | existing Scheduler, policy and dispatcher surfaces | Accept typed intentions, apply policy, order and dispatch work. | Service manager, SQL implementation, Qdrant client or OpenVINO runtime. |
| SQL durable authority | `DbApiSqlContextStore`, `SqlContextRecord`, controlled write/readback tools | Persist typed context and provide authoritative rehydration by `sql_ref`. | Vector index or event bus. |
| Qdrant projection/recall | existing Qdrant projection and recall adapters/tools | Store rebuildable vectors and return references whose payload includes `sql_ref`. | Durable authority. |
| OpenVINO/E5 embedding | existing E5/OpenVINO pipeline and adapter surfaces | Produce explicit normalized embeddings from rehydrated SQL content. | Hidden Scheduler backend or database. |
| RouteProxy fast data plane | existing RouteProxy runtime and frame surfaces | Carry fast request/result frames and readback state. | Policy authority or durable store. |
| EventBus observation | existing EventBus publication surfaces | Publish copies/facts for observation. | Command or authorization path. |
| PassiveSupervisor read model | existing passive supervisor surfaces | Consume accepted facts and expose a read-only view. | Controller or actuator. |
| GitHub workflow surface | scan-once handoff and future gated adapters | Review, workflow and synchronization projection. | Local authority or implicit mutation channel. |
| External process authority | OpenRC, OS and administrator | Start and supervise PostgreSQL, Qdrant and OpenVINO-related services when needed. | Scheduler-owned lifecycle. |

## Validated production-prototype chain

The current one-shot composition is:

```text
0260 real DbApiSqlContextStore write
-> 0261 sql_ref -> SQL rehydrate -> real OpenVINO/E5 embedding
-> 0262 embedding -> Qdrant projection batch with payload.sql_ref
-> 0263 Qdrant recall refs -> unique sql_ref -> SQL rehydrate
-> 0264 closed ResultFrame
-> 0265 EventBus observation-only facts
-> 0266 PassiveSupervisor observation-only read model
-> 0267 local GitHub scan-once handoff, remote_mutation_allowed=False
-> 0268 OpenRC/launcher readiness, services_started=False
-> 0269 one-shot production prototype smoke report
```

A successful 0269 execution requires all nine step reports, propagated
`sql_ref`, `embedding_ref`, `handoff_ref` and `readiness_ref`, and the locked
no-mutation/no-service-start/observation-only boundaries.

References are run-scoped outputs. They prove propagation for one execution; they
are not hard-coded architecture identifiers.

## Backend status

```text
SQL write/readback: real
OpenVINO/E5 embedding: real by default
Qdrant executor in 0269: explicit demo gate
EventBus publication in 0269: explicit in-memory demo gate
GitHub API: not called
GitHub remote mutation: forbidden
OpenRC service start: not called
```

The demo membranes are explicit transition surfaces. They must not be described
as production backends, and replacing them requires a controlled adapter decision
and live validation.

## Compatibility invariants retained from 0154

The 0270 refresh preserves the established authority wording used by the existing
documentation rules:

```text
SQL owns durable context.
Qdrant owns recall projections.
OpenVINO/E5 owns vector generation.
RouteProxy owns fast frames.
```

The validated SQL path continues to use `DbApiSqlContextStore.upsert_record`. The
configured local database resolution contract remains:

```text
1. --db-path
2. AUTODOC_SQL_CONTEXT_DB
3. .var/local/sql_context_store.sqlite3
```

## Reuse-first decisions

Before adding any runtime, handler, adapter, worker or launcher:

1. inspect the current implementation and phase tools;
2. extend or bind an existing surface when its contract is compatible;
3. document the exact gap before adding a new module;
4. keep effects at CLI/IO adapters and immutable contracts in the core;
5. keep `Scheduler.run` unchanged unless a documented exception and dedicated gate exist.

Explicitly avoid parallel `RuntimeManager`, SQL orchestrator, Qdrant adapter,
OpenVINO embedding adapter or GitHub mutation path unless reuse has been proven
impossible.

## Next controlled decisions

1. Complete 0282 mutation plans, explicit adapter authorization and real cycle-history smoke.
2. Continue the controlled real Qdrant executor through existing projection surfaces.
3. Add portable specialist visits/transfers without a laboratory scheduler.
4. Project the complete closed loop into VisPy / Cell Lens observation views.
5. Run Chalouf as the final integrator scenario.

## Canonical companions

- `README.md`
- `doc/architecture/OPERATIONAL_DOCUMENTATION_CONSOLIDATION_0270.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/docs/architecture/00_global.dot` (heritage)
- `doc/docs/architecture/runtime/174_rebuilt_runtime_global_current_state.dot`
- `doc/architecture/GLOBAL_ARCHITECTURE_CURRENT_0282.md`
- `doc/architecture/PROJECTV2_CYCLE_HISTORY_DEVELOPMENT_0282.md`
- `doc/architecture/PROJECT_BEGINNING_CURRENT_COMPARISON_0282.md`
- `doc/code-rules/code_rule.md`
