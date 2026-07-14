# Autodoc / MissiPy — current state and active roadmap

Status date: 2026-07-14.

This document is the current-state and roadmap entrypoint. Historical phase
reports remain evidence but do not override this map.

## Locked architecture boundaries

```text
Scheduler = the only orchestration authority
SQL = durable authority
Qdrant = projection and reference-only recall
OpenVINO multilingual-e5-small = explicit 384-dimensional vectors
/dev/shm = fast local data plane
EventBus = observation only
PassiveSupervisor / VisPy = observation only
GitHub = workflow, review and synchronization surface
OpenRC / OS / administrator = external process authority
```

Laboratories remain independent execution environments behind contracts,
handlers and adapters. They do not own a Scheduler, orchestrator, queue, bus or
parallel registry. Specialists preserve stable identity and context references
across visits and transfers.

`newicody/autodoc` owns the engine, contracts, adapters and source bundle.
Deployed workflows, forms, ProjectV2 fields and views belong to
`newicody/projects`.

## Validated implementation state

The durable walking skeleton is implemented through the existing chain:

```text
SQL write
-> SQL readback
-> OpenVINO/E5 passage embedding (384)
-> Qdrant projection with sql_ref
-> OpenVINO/E5 query embedding (384)
-> Qdrant reference-only recall
-> SQL rehydration
-> closed ResultFrame
-> EventBus / PassiveSupervisor / VisPy observation
```

The GitHub and laboratory chain now includes:

```text
0272 ProjectV2 query-only snapshot, change detection and operator gate
0273 deterministic local fake laboratory
0274 fake laboratory through the existing Scheduler
0275 dual Actions artifacts and laboratory smoke
0276 controlled publication and collision protection
0277 optional non-authoritative Copilot boundary
0281 run-level artifact correlation and controlled publication plan
0282 ProjectV2 cycle lineage/history surfaces
0283 scoped real Qdrant executor factories
0284-r1 reuse audit
0284-r2 portable specialist contract
0284-r3 immutable specialist/laboratory messages
0284-r4 visit and transfer continuity contract
0284-r5 existing-Scheduler portable specialist smoke
0284-r6 real SQL/OpenVINO/Qdrant memory closure
0284-r7 Projects/Copilot/specialist integrated smoke
0284-r8 implementation closure audit
```

The 0284 implementation is complete. It is not considered operationally closed
until one correlated real execution supplies immutable evidence to r8.

## Stable historical compatibility index

Current-state refreshes preserve the validated names consumed by executable
architecture rules. These are traceability anchors and do not roll back the
active 0284/0285 roadmap.

Architecture views retained from 0282:

- `GLOBAL_ARCHITECTURE_CURRENT_0282.md`;
- `PROJECTV2_CYCLE_HISTORY_DEVELOPMENT_0282.md`;
- `PROJECT_BEGINNING_CURRENT_COMPARISON_0282.md`.

The correlated GitHub Actions artifact layout remains:

```text
autodoc-authoritative-request/authoritative_request.json
autodoc-copilot-advisory/copilot_advisory.json
autodoc-dual-artifact-manifest/dual_artifact_manifest.json
```

Validated 0281 milestone names retained for traceability:

- 0281-r2 — dual-artifact run assembly contract;
- 0281-r3 — fetch-once run-group integration;
- 0281-r4 — pinned and cached Copilot CLI runtime;
- 0281-r5 — operator and laboratory advisory projection;
- 0281-r6 — controlled Issue publication;
- 0281-r7 — real closed-loop smoke.

The locked decisions remain: no new Scheduler or parallel orchestrator for
laboratories, and Chalouf as the final integrator scenario.

## Current patch

### 0284-r9 — specialists/laboratories live-path evidence

The patch adds an effect-free evidence use-case and a thin local verifier. It
consumes the stable JSON projection of one already executed 0284-r7 result,
checks correlation and real-backend flags, verifies exact dimension `384`,
loads the required repository source surfaces, then delegates the closure
decision to the existing r8 audit.

It does not execute or mutate Scheduler, SQL, OpenVINO, Qdrant, GitHub or
ProjectV2. A green result proves the run; unit fixtures alone do not claim a
real operational execution.

## Next roadmap

### 0285-r1 — specialist capability growth reuse audit

After a green r9 report, audit the next capability-growth axis before adding a
new provider, specialist family or laboratory framework. Reuse existing
capability, message, transfer, Scheduler routing, durable memory and observation
surfaces first.

### 0285-r2 — capability selection policy

Add immutable capability matching and explicit policy decisions while keeping
the Scheduler as the only orchestration authority.

### 0285-r3 — multi-specialist intervention smoke

Exercise a bounded intervention between portable specialists through the
existing Scheduler and laboratory handlers. Preserve conversation, context,
return route and durable authority.

### 0285-r4 — passive observation replay

Project the correlated multi-specialist path through EventBus,
PassiveSupervisor and VisPy/Cell Lens without introducing command authority.

### 0286 — GitHub Projects operational loop

Stabilize the deployed `newicody/projects` workflow, artifact recovery,
operator decision, controlled publication and ProjectV2 history update. Keep the
cumulative `templates/github/projects-repository/INSTALLATION.md` synchronized
with every useful deployment or configuration change.

### 0288 — Chalouf integrator

Use Chalouf only after the generic path is stable: need intake, research,
portable specialists, cross-validation, synthesis and fabrication planning.

## Development constraints

- one patch at a time;
- audit before adding a module, handler, adapter or runtime;
- extend existing surfaces whenever possible;
- standard library first;
- typed immutable commands, policies and results;
- no business logic in CLI parsing;
- no direct backend call from the kernel;
- no new Scheduler or parallel orchestrator for laboratories;
- SQL remains authority and Qdrant remains projection/recall only;
- E5 dimensions remain exactly 384;
- every phase records code-rule review and live-path status;
- every stable boundary receives executable tests under `tests/rules`;
- every useful Projects deployment change updates the cumulative installation guide.
