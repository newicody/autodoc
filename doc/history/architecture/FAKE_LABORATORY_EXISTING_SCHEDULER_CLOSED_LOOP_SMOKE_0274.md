# Fake laboratory existing-Scheduler closed-loop smoke — 0274-r5

## Purpose

0274-r5 is the final local composition smoke for the fake laboratory path.

It uses **one existing Scheduler** supplied by the platform:

```text
ServerOrientation
-> r2 visits through existing Scheduler
-> fake specialist opinions and synthesis
-> FinalArtifactEnvelope
-> r3 SQL specialist_output
-> r3 E5 passage projection
-> r4 E5 query embedding
-> r4 Qdrant recall refs
-> r4 SQL rehydration
-> closed ResultFrame
-> EventBus facts
-> PassiveSupervisor
-> Cell Lens / VisPy
-> gated GitHub preview
```

No new Scheduler, queue, EventBus, registry or laboratory orchestrator is
created by the smoke module.

## Composition, not authority

The r5 function receives:

- an already-running `SchedulerContract`;
- the existing SQL store;
- a controlled passage embedding profile;
- an embedding callable;
- a controlled Qdrant projection executor;
- a recall-executor factory;
- optionally, the existing EventBus.

It only calls the r2, r3 and r4 functions in order. Scheduler startup and
shutdown remain owned by the normal platform bootstrap.

## Semantic closure

The smoke validates that:

- r2 produced a converged `FinalArtifactEnvelope`;
- r3 persisted one immutable `specialist_output`;
- r3 acknowledged a passage projection;
- r4 recalled the same `sql_ref`;
- SQL rehydrated the exact specialist output;
- the laboratory `ResultFrame` carries the same final and synthesis refs;
- PassiveSupervisor and visual models are present;
- the GitHub preview remains pending behind the publication gate.

## Replay gate

When enabled, r5 performs a second r3 SQL handoff without another vector write.

The replay must report:

```text
idempotent_replay = true
inserted = false
replaced = false
qdrant_write_performed = false
```

This proves immutable durable reuse without claiming that a remote backend is
idempotent.

## Authority boundaries

- Scheduler remains the single orchestration authority.
- SQL remains durable authority.
- OpenVINO/E5 creates passage and query vectors only.
- Qdrant remains projection and recall only.
- EventBus remains observation-only.
- PassiveSupervisor remains passive.
- Cell Lens and VisPy remain passive renderers.
- GitHub remains a local preview and review surface.
- Remote mutation still requires the existing publication gate.

## Runtime claim

The fake provider and demo executors remain test doubles:

```text
live_path_uses_real_backend = false
live_backend_claimed = false
```

R5 proves composition and contracts, not production backend readiness.

## Next phase

0275 will leave the fake-only local loop and address the real GitHub exchange:

```text
authoritative GitHub request artifact
+ separate Copilot advisory artifact
-> local intake and SourceCandidate
-> laboratory path
-> reviewed return artifact
```

The two artifacts must remain separate, and GitHub mutation must remain behind
an explicit operator gate.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.laboratory.v1
context_contract_changed: false
external_dependencies_added: false
scheduler_created: false
scheduler_modified: false
scheduler_run_owned: false
parallel_orchestrator_created: false
parallel_queue_created: false
parallel_eventbus_created: false
parallel_registry_created: false
sql_replay_verified: true
github_mutation_performed: false
network_added: false
```
