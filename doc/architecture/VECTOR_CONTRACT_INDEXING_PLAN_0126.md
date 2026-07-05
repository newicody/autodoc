# 0126 — Vector contract indexing plan

0126 locks the vector contract indexing direction.

One Qdrant instance, multiple role-oriented collections. Do not create one Qdrant database per specialist in 0126.

The initial collections are:

- `context_chunks_e5_384`
- `contracts_e5_384`
- `specialist_outputs_e5_384`
- `deliberation_signals_e5_384`
- `synthesis_candidates_e5_384`

Qdrant links context, contracts, opinions, signals, and synthesis candidates; it does not decide. SQLContextStore is durable context authority. Scheduler remains the orchestrator of deliberation. GitHub exchanges artifacts only.

## Why collections are role-oriented

A specialist can be material, thermal, psycho-social, safety, synthesis, documentation, or another future worker. Splitting one Qdrant database per specialist would fragment context and make cross-specialist synthesis harder.

Instead, specialist identity is payload/filter metadata. The same collection can answer:

- which contracts are relevant to this demand;
- which context chunks should be rehydrated from SQL;
- which previous specialist outputs are semantically near;
- which bus/search signals indicate already explored paths;
- which pieces are good synthesis candidates.

## E5/OpenVINO role

E5/OpenVINO indexes contracts and specialist outputs behind adapter. It is embedding only, not decision maker.

The locked usage is:

```text
SQL contract
-> passage: specialist instruction contract ...
-> E5/OpenVINO adapter
-> qdrant:contracts_e5_384
```

and:

```text
Specialist demand
-> query: ...
-> E5/OpenVINO adapter
-> Qdrant recall across role collections
-> SQL rehydration
-> Scheduler-dispatched specialist work
```

## Contracts as first-class context

Specialist instruction contracts are persisted in SQL and indexed as passages. They describe:

- specialist domain;
- objective;
- expected machine result;
- expected human representation;
- required evidence/context refs;
- output type.

Specialists produce machine_result plus human_representation. The machine layer is suitable for recomposition, deliberation, and future replay. The human representation layer is a proposed end-user surface that can be hidden, transformed, or unified by the final synthesis.

## Boundary lock

- Scheduler remains the orchestrator of deliberation.
- `/dev/shm` route frames remain the multitask data-plane interface.
- EventBus observes facts, paths, and statistics.
- SQLContextStore is durable context authority.
- Qdrant is vector projection and retrieval, not context authority.
- E5/OpenVINO is embedding only behind adapter.
- GitHub exchanges artifacts only.
- No runtime client is introduced in 0126.
