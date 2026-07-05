# 0127 — Vector collection registry

VectorCollectionRegistry turns 0126 roles into a local collection registry.

## Locked direction

One Qdrant instance, multiple role-oriented collections.

Do not create one Qdrant database per specialist in 0127. Specialist identity is a payload/filter dimension and a SQL ref dimension, not a separate database boundary.

The registry produces collection ensure plans only. The adapter executes collection creation later; this patch does not import or call qdrant-client.

## Boundaries

- Scheduler remains the orchestrator of deliberation.
- SQLContextStore is durable context authority.
- E5/OpenVINO remains embedding only behind adapter.
- Qdrant is projection and recall only; it does not decide.
- GitHub exchanges artifacts only.
- EventBus observes statistics and paths, not payloads.
- route /dev/shm remains multitask data-plane interface.

## Collections

The registry keeps the 0126 role collections:

- `context_chunks_e5_384`
- `contracts_e5_384`
- `specialist_outputs_e5_384`
- `deliberation_signals_e5_384`
- `synthesis_candidates_e5_384`

## Runtime path later

The future runtime adapter can consume `VectorCollectionEnsurePlan` and create/update collections in the local Qdrant service. That adapter is still outside the kernel and outside the Scheduler.

The Scheduler only schedules the work. The route `/dev/shm` frames move fast local multitask data. SQL persists durable truth. Qdrant receives lightweight payload refs and vectors.
