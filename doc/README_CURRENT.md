# Autodoc / MissiPy — current state and active roadmap

Status date: 2026-07-15.

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
0284-r1 through r9 portable specialists and correlated live-path evidence
0285-r1 through r8 specialist capability-growth closed loop
0286-r1 through r8 operator-authorized Projects capability-growth loop
0287-r1 through r7 multi-laboratory evidence aggregation and durable history
0287-r7-r1 controlled local Copilot advisory ProjectV2 publication path
```

The generic 0284, 0285 and 0286 chains are closed by correlated evidence. The
active development objective is now to make the complete GitHub-to-local-to-
ProjectV2 path operational, repeatable and covered by positive and negative
end-to-end tests.

## Stable historical compatibility index

Current-state refreshes preserve the validated names consumed by executable
architecture rules. These are traceability anchors and do not roll back the
active 0287 roadmap.

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
laboratories. No product-specific integrator phase is scheduled. Development
stays focused on the generic end-to-end path and its operational evidence.

Historical compatibility marker: `Chalouf as the final integrator scenario`.
This exact legacy token is retained only for executable documentation rules;
it is retired from the active roadmap and does not schedule a phase 0288.

## Current patch

### 0287-r7-r2 — Copilot first-opinion advisory v2

The existing Copilot runner already receives the Issue title, body and labels.
This patch corrects the public response contract rather than reinterpreting
`missipy.github.copilot_advisory.v1`.

New runs produce `missipy.github.copilot_advisory.v2`. Its analytical content is
limited to four fields:

1. `concrete_objective`;
2. `expected_result`;
3. `provided_constraints`;
4. `success_criteria`.

The historical v1 extraction helper remains available during migration, while
the active producer emits v2 only. Copilot remains optional, tool-denied,
untrusted and unusable as publication authority.

## End-to-end operational roadmap

### 0287-r7-r3 — v1/v2 consumer migration

Audit every durable reader of `copilot_advisory.json`. Add explicit v1 and v2
normalization at existing boundaries, migrate active consumers to the four v2
fields and keep historical v1 artifacts readable. No new manager or adapter is
introduced unless the reuse audit proves one is required.

### 0287-r7-r4 — v2 publication-preview bridge

Map the four v2 analysis fields into the existing operator preview and ProjectV2
projection. Keep the preview effect-free and preserve policy decision, exact
`plan_digest`, mutation locks and `--execute` requirements.

### 0287-r7-r5 — deterministic full local end-to-end smoke

Exercise one correlated chain with controlled fixtures:

```text
Issue envelope
-> authoritative request
-> Copilot advisory v2
-> dual-artifact manifest
-> artifact fetch and run assembly
-> source-candidate intake
-> explicit operator decision
-> existing-Scheduler fake laboratory
-> publication preview
```

Prove identifiers, digests, lineage and authority boundaries at every hop.

### 0287-r7-r6 — controlled remote publication and readback smoke

Execute the accepted plan against `newicody/projects` with both mutation locks,
the exact confirmed digest and explicit operator approval. Verify ProjectV2 or
Issue readback, collision protection and idempotent replay.

### 0287-r7-r7 — real Copilot and Actions evidence

Run a non-trivial Issue through the deployed workflow. Recover the three
correlated artifacts, verify that the four v2 fields contain a concrete first
opinion, and prove that advisory absence still leaves the authoritative request
usable.

### 0287-r7-r8 — recovery and negative-path matrix

Cover disabled Copilot, timeout, command failure, malformed JSON, wrong schema,
stale digest, mismatched correlation, duplicate publication, network failure,
restart, replay and retry. Every failure must be observable and fail closed at
the appropriate authority boundary.

### 0287-r7-r9 — installation and deployment closure

Compare `templates/github/projects-repository/` with the deployed private
`newicody/projects` repository using preview-first synchronization and
`git diff`. Verify Actions policy, variables, token availability, ProjectV2
identity and OpenRC/local fetch configuration without storing secrets in Git.

### 0287-r7-r10 — generic operational closure

Run the complete green matrix with deterministic fixtures and one controlled
real execution. Close only when the end-to-end path is repeatable, documented,
recoverable, observable and idempotent. No Chalouf or other product-specific
phase follows this closure.

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
