# Phase 0287-r7-r15-r3-r8 — Async hybrid retrieval execution

## Result

The installed love path can now await an asynchronous dense E5 embedder and
reuse the complete r8-r4 hybrid retrieval composition without duplicating its
profile validation, dense/sparse search, fusion or SQL rehydration logic.

A one-shot synchronous bridge exposes only the already-computed embedding to the
existing composition and refuses reuse for another query identity.

## Boundaries

- the existing hybrid composition remains authoritative;
- no second event loop is started;
- no Scheduler, Qdrant client or SQL store is constructed;
- Qdrant and SQL remain injected ports;
- raw dense values are absent from the async execution receipt;
- installed E5 dimension remains 384.

## Next unit

The next unit is the **Qdrant hybrid adapter**. It will adapt the existing real
Qdrant client executor to `search_dense()` and `search_sparse()` while preserving
reference-only payloads and SQL authority.
