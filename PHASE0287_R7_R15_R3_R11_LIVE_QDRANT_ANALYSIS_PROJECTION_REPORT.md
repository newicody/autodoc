# Phase 0287-r7-r15-r3-r11 — Live Qdrant analysis projection

## Result

One already-persisted SQL authority object can now be projected asynchronously through the installed E5 pipeline and the existing qdrant-client membrane.

- dense passage vector: `dense_e5_v1`, 384 dimensions, normalized;
- sparse lexical vector: `sparse_lexical_v1`, built by the exact retrieval-side lexical function;
- physical collection: `autodoc_context_e5_384_hybrid_v1`;
- one deterministic point upsert behind the existing write gate;
- reference-only payload;
- reconstructible projection metadata stored separately in SQL.

No Scheduler, collection lifecycle, alias mutation or SQL connection is created here.

## Next

Compose one controlled live projection command that opens the existing PostgreSQL authority, installed E5 pipeline and Qdrant executor, then verifies readback and SQL rehydration for one point.
