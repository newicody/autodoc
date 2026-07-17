# Phase 0287-r7-r15-r3-r10 — Qdrant named collection control

## Result

The installed runtime can now plan, inspect and explicitly create one physical
hybrid Qdrant collection with:

- dense vector `dense_e5_v1`, dimension 384, Cosine;
- sparse vector `sparse_lexical_v1`;
- the canonical SQL-reference payload indexes created before ingestion.

The plan is deterministic and digest-addressed. Execution requires an approved
operator decision, an explicit mutation environment gate and an exact confirmed
plan digest.

## Compatibility

Legacy manual configurations without explicit dense/sparse vector names keep the
previous unnamed-vector read-only readiness behavior. Named mode is enabled only
when both vector-name keys are present.

## Safety boundaries

- no collection deletion;
- no payload-index deletion;
- no alias mutation or alias swap;
- no point upsert;
- no Scheduler, OpenVINO or PostgreSQL construction;
- no secret serialization;
- SQL remains the durable authority.

The physical collection is `autodoc_context_e5_384_hybrid_v1`. Alias activation
for `autodoc_context_hybrid_current` is deliberately deferred until projection
and readback are validated.

## Validation

- isolated tests: 7 passed;
- legacy unnamed readiness compatibility checked;
- Python compilation checked.

## Next unit

The next unit implements named dense+sparse projection into the validated
physical collection while keeping point payloads reference-only.
## r10-r1 compatibility correction

Legacy direct constructors now receive safe defaults for the new named-vector fields.
