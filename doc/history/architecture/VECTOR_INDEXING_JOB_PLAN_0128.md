# 0128 — Vector indexing job plan

VectorIndexingJobPlan schedules E5/OpenVINO embedding and Qdrant projection without executing either.

This phase converts the 0126 vector contract plan and the 0127 collection registry into Scheduler-addressable indexing jobs.  It is still a contract layer: it prepares bounded work for adapters and workers, but it does not import or call OpenVINO, Qdrant, PostgreSQL, GitHub, HTTP, sockets, VisPy, or any daemon.

## Locked boundary

- Scheduler remains the orchestrator of vector indexing jobs.
- route /dev/shm is the multitask data-plane interface and future grid seam.
- SQLContextStore is durable context authority.
- E5/OpenVINO remains embedding only behind adapter.
- Qdrant is projection and recall only; it does not decide.
- one Qdrant instance with role-oriented collections, not per-specialist databases.
- EventBus observes vector indexing statistics and paths, not payloads.
- GitHub exchanges artifacts only.
- Specialist identity stays payload/filter metadata.

## Flow

```text
VectorIndexableItem
-> SchedulerVectorIndexingBatchCommand
-> VectorEmbeddingJob
-> /dev/shm embedding request frame
-> E5/OpenVINO adapter later
-> /dev/shm embedding result frame
-> VectorProjectionJob
-> /dev/shm projection request frame
-> Qdrant adapter later
-> role-oriented Qdrant collection
-> SQL ref remains authority
```

## What is stored where

```text
SQL
  durable content, contracts, specialist outputs, synthesis candidates

E5/OpenVINO
  embedding computation only, behind adapter

Qdrant
  vector projection and recall, payload refs only

/dev/shm route frames
  multitask local exchange, future grid seam, not authority

EventBus
  vector indexing statistics, paths, scheduling facts, no heavy payloads
```

## Why not one Qdrant per specialist

The registry keeps one Qdrant instance with role-oriented collections:

```text
context_chunks_e5_384
contracts_e5_384
specialist_outputs_e5_384
deliberation_signals_e5_384
synthesis_candidates_e5_384
```

Specialist identity remains payload/filter metadata.  This allows recall across specialists when the Scheduler requests contradiction search, convergence search, or final synthesis.

## Phase status

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0128 adds a pure contract/use-case layer and follows existing backend membrane rules.
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: true
```
