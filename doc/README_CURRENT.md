# Autodoc / MissiPy — current state and active roadmap

Status date: 2026-07-13.

This document is the detailed current-state and roadmap entrypoint. The root
README remains stable and general. Historical phase documents remain evidence;
they do not override this current map.

## Locked architecture boundaries

```text
Scheduler = the only orchestration authority
SQL = durable authority
Qdrant = projection and recall only
OpenVINO/E5 = explicit vector generation
/dev/shm = fast data plane
EventBus = observation only
PassiveSupervisor / VisPy = observation only
GitHub = workflow, review and synchronization surface
OpenRC / OS / administrator = external process authority
```

Laboratories are independent execution environments behind contracts, handlers
and adapters. They do not own a scheduler, orchestrator, queue, bus or registry.
The fake laboratory must continue to use the existing Scheduler path.

The `autodoc` repository contains source, templates, contracts and validation.
Automation settings and deployed workflow configuration belong to the external
`newicody/projects` repository.

## Validated operational milestones

The durable and recall walking skeleton is validated through the existing
0260-0269 chain:

```text
SQL write
-> SQL rehydrate
-> OpenVINO/E5 embedding
-> Qdrant projection with sql_ref
-> Qdrant recall refs
-> SQL rehydrate
-> closed ResultFrame
-> EventBus observation
-> PassiveSupervisor projection
```

The GitHub and laboratory continuation has reached:

```text
0272 ProjectV2 query-only snapshot, change detection and operator gate
0272 durable SourceCandidate consumer and closed-loop smoke
0273 deterministic fake laboratory provider
0274 fake laboratory closed loop through the existing Scheduler
0275 dual-artifact contract, workflow, read-only intake and laboratory smoke
0276 controlled publication boundary, contract and collision protection
0277 optional Copilot execution boundary
0278 controlled event-path boundary
0279 structured Copilot response extraction
0280 GitHub template Python syntax gate
```

A real GitHub Actions run now creates all three correlated artifacts:

```text
autodoc-authoritative-request/authoritative_request.json
autodoc-copilot-advisory/copilot_advisory.json
autodoc-dual-artifact-manifest/dual_artifact_manifest.json
```

The authoritative request remains the authority. The Copilot advisory is
consultative only. Its content must remain available for specialist/laboratory
context and operator review without being copied into authoritative state.

## Current gap

The generic 0168 fetcher downloads and synchronizes each Actions artifact
separately. The existing 0275 intake already validates the request, optional
advisory, manifest, SHA-256 digests and correlation identifiers, but the fetch
path does not yet assemble the three artifacts at run level and call that
intake automatically.

Consequences:

- raw files can be downloaded and stored;
- the full Copilot advisory exists in the raw artifact;
- semantic correlation is not yet an automatic fetch result;
- the advisory is not yet handed to the existing laboratory path;
- no controlled advisory summary is yet published to the Issue.

The workflow also installs the Copilot CLI npm tree on each GitHub-hosted run.
This is operationally redundant and must be replaced by a pinned, cached local
prefix, installed only on a cache miss.

## Active roadmap

### 0281-r2 — dual-artifact run assembly contract

Audit and reuse:

- `tools/run_github_actions_artifact_fetch_once.py`;
- `tools/run_github_artifact_server_sync_once.py`;
- `src/context/github_dual_artifact_source_candidate_intake_0275.py`;
- `src/context/github_dual_artifact_laboratory_smoke_0275.py`.

Add a typed, immutable run-assembly command/policy/result that:

- groups files by repository and Actions run;
- recognizes the authoritative request, optional advisory and manifest;
- rejects duplicates and ambiguous members;
- calls the existing 0275 intake;
- preserves the complete advisory as a non-authoritative artifact reference;
- performs no SQL write, Qdrant write, GitHub mutation or Scheduler change.

`live_path_status` remains `transition` until the fetcher invokes this use-case.

### 0281-r3 — fetch-once run-group integration

Extend the existing 0168 fetch surface rather than creating a second fetcher.

- preserve raw per-artifact dataset synchronization;
- assemble only after all matching artifacts for a run are downloaded;
- make replay idempotent by repository/run/manifest identity;
- write a stable intake report and observation event;
- mark the run semantically ingested only after successful correlation;
- keep network access in the existing GitHub adapter boundary.

### 0281-r4 — pinned and cached Copilot CLI runtime

Update the existing workflow template and external deployment:

- pin the Copilot CLI version;
- install under a workflow-local prefix;
- restore the complete prefix from cache;
- run npm installation only on cache miss;
- keep `GITHUB_TOKEN` scoped to the job;
- keep Copilot tools denied by default;
- retain a non-blocking mode only when policy says advisory is optional.

The selected-actions policy in `newicody/projects` must explicitly allow the
GitHub-owned cache action version used by the workflow. Automation parameters
remain outside the `autodoc` source repository.

### 0281-r5 — operator and laboratory advisory projection

Reuse the existing SourceCandidate gate and fake laboratory closed loop:

```text
validated run intake
-> SourceCandidate
-> explicit promote or merge decision
-> existing Scheduler
-> fake laboratory
-> publication preview
```

The laboratory may read the advisory as a hint through an artifact/context
reference. It must not reinterpret it as authority and must not create a second
scheduler or orchestration path.

### 0281-r6 — controlled Issue publication

Reuse the existing 0276 publication boundary and collision guard.

- publication requires an explicit operator-authorized decision;
- publish an idempotent marker-based comment or update;
- include advisory summary, proposed route, questions, risks and confidence;
- label the advisory clearly as consultative and non-authoritative;
- never publish raw secrets, tokens, transport logs or hidden prompts;
- do not let a GitHub Actions producer self-authorize publication.

### 0281-r7 — real closed-loop smoke

Validate one real Issue through:

```text
Issue
-> three Actions artifacts
-> local read-only fetch
-> run-level correlation and intake
-> operator gate
-> existing-Scheduler fake laboratory
-> controlled publication preview
-> authorized idempotent Issue publication
```

The phase closes only when replay, missing-advisory mode, duplicate artifacts,
digest mismatch, publication collision and no-mutation defaults are tested.

## Following roadmap

After the 0281 GitHub/laboratory walking skeleton is green:

1. ProjectV2 cycle history, parent/sub-ticket links and theme grouping;
2. controlled real Qdrant executor continuation through existing surfaces;
3. portable specialist visits/transfers between laboratories using
   `laboratory_ref`, `origin_laboratory_ref`, `target_laboratory_ref`,
   `visit_ref`, `specialist_ref`, `conversation_ref`, `context_refs`,
   `return_route_ref`;
4. VisPy/Cell Lens projection of the complete closed loop;
5. Chalouf as the final integrator scenario for need intake, research,
   specialist contracts, cross-validation, synthesis and fabrication planning.

## Development constraints

- one patch at a time;
- audit before adding a module, handler, adapter or runtime;
- extend an existing surface whenever possible;
- standard library first;
- typed immutable commands, policies and results;
- no business logic in CLI parsing;
- no direct GitHub, SQL, Qdrant, OpenVINO or LLM call from the kernel;
- no new Scheduler or parallel orchestrator for laboratories;
- every phase records code-rule review and live-path status;
- every stable boundary receives executable tests under `tests/rules`.
