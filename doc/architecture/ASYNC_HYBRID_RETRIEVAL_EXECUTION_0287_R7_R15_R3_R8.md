# Async hybrid retrieval execution

```text
async E5 query adapter
        |
        | await embed_query()
        v
precomputed dense embedding bridge
        |
        v
existing execute_hybrid_retrieval()
        |-- existing Qdrant port
        `-- existing SQL authority reader
```

The bridge is one-shot and query-bound. The r8-r4 composition remains the only
implementation of collection validation, sparse query creation, fusion,
grouping and SQL-authoritative rehydration.
