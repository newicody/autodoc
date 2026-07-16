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

## Product-final reuse audit and authoritative roadmap adaptation

### 0287-r7-r5 — specialist exchange, synthesis and product-chain reuse audit

This section is the authoritative continuation after 0287-r7-r4. The earlier
r5-r10 walking-skeleton order is retained above as a compatibility record, but
it is superseded for active development by the product-final order below.

The target user-visible chain is:

```text
source Issue / ProjectV2 item
-> authoritative research-context artifact
-> Copilot advisory v2 artifact
-> controlled advisory projection visible on the board
-> local fetch and correlated research work package
-> explicit operator decision
-> existing Scheduler
-> concrete native laboratory
-> two domain specialists producing deep analyses
-> later liaison synthesis and final artifact envelope
-> controlled deliverable publication on the source Issue
-> ProjectV2 readback, durable evidence and idempotent replay
```

The first concrete laboratory prototype is
`laboratory:love-studies-local`. It executes two simple but real specialists:

- `specialist:love-concept-and-affect-analyst`;
- `specialist:love-relational-dynamics-analyst`.

Their primary responsibility is deep domain analysis. A specialist may produce
a local synthesis when its mission explicitly asks for one, but the default
mutualized synthesis happens later through the existing liaison boundary.

### Reuse decisions locked by r7-r5

The existing `missipy.specialist.laboratory_message.v1` contract already owns
message identity, conversation identity, sequence ordering, request/reply
links, route references, context references, evidence references and immutable
payloads. It must be extended through an explicit v2 migration; no unrelated
`SpecialistExchangeEnvelope` module is to be invented.

The following existing surfaces remain canonical and must be extended rather
than replaced:

- `specialist_laboratory_message_contract_0284.py` for specialist/laboratory
  exchanges and ordered conversations;
- `specialist_laboratory_transfer_contract_0284.py` for cross-laboratory
  continuity;
- `server_oriented_deliberation_cycle.py` for orientation, specialist demands,
  rounds and the final artifact envelope;
- `specialist_liaison_synthesis.py` for fragments, liaison synthesis and final
  synthesis packets;
- `portable_specialist_real_memory_closure_0284.py` for SQL-authoritative,
  OpenVINO/E5-384 and Qdrant-reference-only memory closure;
- the 0287 multi-laboratory evidence aggregation, provenance, contradiction,
  operator-weighting and durable-history chain;
- the existing controlled GitHub publication planners, collision guards,
  digest confirmation and readback adapters.

The deterministic fake laboratory remains test evidence only. It must not be
silently renamed or converted into the concrete laboratory. A distinct native
provider is justified because the existing provider explicitly declares
`provider_kind=local_fake` and `real_backend_used=false`.

### Current connection status

```text
Issue -> dual Actions artifacts                         implemented
Copilot v2 artifact                                    implemented
Copilot v2 projection through local intake             implemented
Copilot v2 visible on ProjectV2 / source Issue         controlled adapters implemented
periodic artifact fetch -> one research work package   partial
research work package -> concrete laboratory           not connected
portable specialist/message/multitask contracts         implemented contracts
real domain specialist execution                       absent
liaison synthesis contracts and final envelope         implemented contracts
real specialist analyses -> liaison synthesis          not connected
SQL/E5/Qdrant specialist memory closure                implemented separately
0287 multi-laboratory evidence chain                   implemented separately
final deliverable -> source Issue publication          absent
publication-surface readback/replay                     implemented; full-chain proof pending
```

### Adapted product-final roadmap

#### 0287-r7-r6 — Copilot advisory v2 board and Issue projection

Extend the existing publication planners and Projects scripts to render the
four v2 fields, preserve the advisory artifact reference, compute an exact plan
digest, publish only the advisory projection, and verify idempotent readback.
No Copilot output may change an authoritative status or operator decision.

Closure status: implemented as versioned preview, ProjectV2 projection and
controlled source-Issue publication adapters. The v2 ProjectV2 path writes the
four analytical values into the generic `Avis Copilot` field and deliberately
leaves historical route/confidence fields untouched. Both ProjectV2 field and
Issue comment adapters perform immediate exact readback; the private live-board
evidence remains part of the real closed-loop smoke.

#### 0287-r7-r7 — correlated research work package

Close fetch, run assembly and intake into one immutable package containing the
authoritative request, Copilot advisory, manifest, attachment references,
context references, success criteria, source Issue and return route. The
package is the input to specialist work; Copilot remains hint-only.

Closure status: implemented as `missipy.research.correlated_work_package.v1`.
The builder consumes the validated 0281 run assembly, preserves the request and
advisory in their public schemas, correlates fetched attachment references by
Issue/frame/revision/run, excludes raw bytes and local paths, and creates no
Scheduler route or durable write. The package is ready for the message/analysis
contract in r8.

#### 0287-r7-r8 — specialist/laboratory message v2 and analysis contribution

Version and extend the existing message contract with explicit artifact
references and digests, correlation/idempotency identity, completion and error
messages, and cross-visit continuation. Define a generic deep-analysis
contribution contract that maps deterministically into
`SpecialistOutputFragment` without forcing early global synthesis.

Closure status: implemented as the explicit companion schemas
`missipy.specialist.laboratory_message.v2`,
`missipy.specialist.laboratory_conversation.v2`,
`missipy.specialist.deep_analysis_request.v1` and
`missipy.specialist.deep_analysis_contribution.v1`. The historical v1 message
module remains unchanged and readable. V2 adds digest-backed artifact
references, stable correlation/idempotency identities, normalized completion
and error messages, and continuation across visits and specialists. Deep
analysis contributions retain findings, evidence, uncertainties, contradictions,
limitations and recommendations for the later liaison synthesis; no global
synthesis is inferred unless the mission explicitly requests it.

##### 0287-r7-r8-r1 — extensible multitask specialist model

Keep the portable descriptor and the r8 message/deep-analysis contracts as
stable foundations, then add a generic task layer. A specialist declares more
than one versioned task type, each task invokes one explicit capability, and a
Scheduler-owned acyclic plan may expose independent tasks for controlled
parallel execution. Specialists may propose follow-up tasks or another
specialist, but they never create or execute those tasks directly.

Closure status: implemented as `missipy.specialist.task_type.v1`,
`missipy.specialist.task_request.v1`, `missipy.specialist.task_plan.v1`,
`missipy.specialist.task_result.v1` and
`missipy.specialist.multitask_definition.v1`. The existing deep-analysis
request/contribution pair is projected into this generic envelope as
`specialist-task-type:analysis.deep`; it is not replaced. Existing OpenVINO
execution is referenced through `missipy.specialist.task_execution_binding.v1`
without importing or reimplementing OpenVINO. No global registry, Scheduler,
worker, queue, laboratory runtime or model runtime is created.

The following context/storage boundaries precede the domain specialists:

- `0287-r7-r8-r2`: SQL-authoritative context revisions, relations, artifacts
  and vector-projection metadata;
- `0287-r7-r8-r3`: canonical Qdrant payload, named-vector, filter and index
  profile while SQL remains authority;
- `0287-r7-r8-r4`: dense E5 plus sparse retrieval, grouping, optional reranking
  and SQL rehydration;
- `0287-r7-r8-r5`: Scheduler-controlled snapshot, checkpoint-rebase, restart
  and fork policies for significant context revisions;
- `0287-r7-r8-r6`: ControlProxy transport of authorized notifications or route
  changes only; the proxy does not own knowledge or semantic revisions.

##### 0287-r7-r8-r2 — context revision SQL authority

Keep `missipy.sql_context_store.v1` unchanged for historical records and add a
versioned companion authority for semantic context DAGs. SQL now has an
executable DB-API schema for authority objects, content-addressed artifact
metadata, multi-parent revisions, complete membership snapshots, graph
relations and vector-projection provenance. An explicit bridge imports a
historical `SqlContextRecord` without changing its identity or original store.

The store records source digests, embedding profiles, model revisions,
collections, named vectors and point identifiers, but never raw vector values,
MMIO addresses or mmap pointers. Heavy bytes remain behind content-addressed
storage references. Qdrant stays reconstructible, the Scheduler remains the
impact authority. ControlProxy route generations remain transport state
only. This phase does not call OpenVINO, mutate Qdrant, alter Scheduler routes,
publish EventBus events or change GitHub.

Closure status: executable SQL/SQLite boundary and targeted tests implemented;
production-chain wiring intentionally deferred. The next phase defines the
canonical Qdrant payload, named-vector and filter/index profile over this SQL
authority.

##### 0287-r7-r8-r3 — canonical Qdrant profile

Define shared point identity, dense/sparse/multivector named spaces, canonical
reference payloads, payload indexes and model migration plans. SQL remains the
authority and no Qdrant mutation occurs in this contract-only phase.

Closure status: implemented and validated. The active E5 projection is exposed
as `dense_e5_v1`; future sparse and late-interaction representations share the
same point only when they represent the same SQL-authoritative object.

##### 0287-r7-r8-r4 — hybrid retrieval and SQL rehydration

Compose the existing E5/OpenVINO query embedding boundary with dense and sparse
Qdrant named-vector searches under one revision/branch/project/security scope.
Fuse candidates by reciprocal rank, group them by document, contribution or
source, then accept content only after active-membership and digest validation
against the r8-r2 SQL authority.

Closure status: executable composition implemented behind injected ports. Raw
dense vectors are not serialized, Qdrant payloads remain reference-only, and
no Qdrant write, Scheduler, EventBus or ControlProxy mutation is introduced.

##### 0287-r7-r8-r5 — context revision task-impact policy

Bind each specialist task to one accepted SQL semantic revision and one explicit
update policy. Build a reference-only change set for a direct accepted child
revision, assess dependency and significance impact, then produce an effect-free
Scheduler decision proposal.

The supported policies are `snapshot`, `checkpoint_rebase`,
`restart_on_material_change`, `fork_on_material_change`, `notify_only` and
`ignore_noncritical`. A completed result is never rewritten; it remains
reproducible against its original revision and may be marked stale against the
new revision. Every decision declares that no task, route or event has yet been
created or changed.

Closure status: contracts, deterministic policy composition and tests are
implemented. SQL semantic revision remains authority, Scheduler decision remains
the only execution authority, EventBus remains observation-only and ControlProxy
remains transport-only. The next unit is `0287-r7-r8-r6`, which applies accepted
Scheduler decisions through existing execution/observation boundaries and uses
ControlProxy only when an authorized notification or route transition is needed.

##### 0287-r7-r8-r6 — authorized context-impact execution

Execute an immutable r8-r5 impact plan only after an explicit Scheduler policy
authorization and exact plan digest verification. The existing Dispatcher event
boundary receives `CONTEXT_IMPACT_EXECUTION`; a Scheduler-owned task mutation
port applies idempotent rebind, checkpoint rebase, restart, fork and stale-result
transitions. EventBus receives an observation result and affected laboratories
receive Scheduler-issued context-update notifications.

ControlProxy is called only for an explicit transport transition declared by the
execution target and only through the existing
`missipy.scheduler.route_adapter_request.v1` boundary. A semantic context change
never implies a route change by itself. SQL remains the knowledge authority,
EventBus remains observation-only, and no Scheduler, queue, laboratory manager or
parallel orchestrator is added.

Closure status: executable handler, task mutation reference port, route-adapter
seam, laboratory notifications, event types, digest authorization, replay and
negative-path tests are implemented. The next unit is
`0287-r7-r9 — love-study contracts and specialist descriptors`.

#### 0287-r7-r9 — love-study contracts and specialist descriptors

Define the input, attributable findings, two domain-analysis outputs and
prototype result contracts. Declare `laboratory:love-studies-local` as a disabled
`autodoc_native` laboratory descriptor and declare two portable, extensible,
multitask specialists. Their primary outputs are deep domain analyses; local
synthesis is an explicit optional task and global synthesis remains a later
liaison step.

Closure status: implemented as contract-only. The laboratory is declared but no
provider, handler, Scheduler registration, OpenVINO runtime, SQL/Qdrant write or
GitHub mutation is created. `0287-r7-r10` attaches the concrete native provider
through the existing Scheduler-owned registry and implements the first real
specialist handler.

#### 0287-r7-r10 — concrete native laboratory and first specialist

Register `laboratory:love-studies-local` behind the existing Scheduler-owned
registry and execute `specialist:love-concept-and-affect-analyst`. The
specialist performs real deterministic text analysis and produces evidence,
uncertainties and a versioned analysis artifact.

#### 0287-r7-r11 — second specialist and Scheduler-controlled collaboration

Execute `specialist:love-relational-dynamics-analyst`. It consumes the research
package and authorized artifacts from the first analysis through the versioned
message contract. Any request for more context or another specialist returns to
the existing Scheduler; specialists never invoke each other directly.

#### 0287-r7-r12 — memory, evidence and liaison synthesis integration

Persist authoritative analyses in SQL, project and recall references through
OpenVINO/E5-384 and Qdrant, connect the 0287 evidence/contradiction/weighting
chain, then map accepted analyses into the existing liaison synthesis and final
artifact envelope. Contradictions and unresolved points must remain visible.

#### 0287-r7-r13 — final deliverable publication plan

Render the final artifact envelope as deterministic human-readable Markdown,
build a distinct deliverable marker and plan digest, and prepare controlled
publication on the source Issue plus a concise ProjectV2 status/readback
projection. This path is separate from the initial Copilot advisory comment.

#### 0287-r7-r14 — full deterministic local smoke

Exercise Issue fixture, three GitHub artifacts, fetch/assembly, operator gate,
concrete laboratory, two real specialists, durable analyses, liaison synthesis,
final deliverable, publication preview and simulated readback in one correlated
local proof.

#### 0287-r7-r15 — real GitHub Actions closed-loop evidence

Run one real source Issue through the deployed workflow, advisory board
projection, local fetch, concrete laboratory, two specialists, final synthesis,
controlled source-Issue publication and ProjectV2/Issue readback.

#### 0287-r7-r16 — recovery, installation and prototype closure

Close disabled/invalid Copilot, missing or mismatched artifacts, specialist
failure, timeout, restart, replay, duplicate/collision, stale digest, network
failure and partial publication. Verify OpenRC/fcron deployment, compare the
Projects source bundle with the deployed repository, run the global suite and
prove installation from a clean checkout.

The prototype is complete only when the full real chain is repeatable,
observable, recoverable and idempotent. There is no phase 0288 and no Chalouf
integrator phase.
