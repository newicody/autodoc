# 0271-r5 — Qdrant SQL-authority scope live binding

## Purpose

Bind the reusable 0271-r4 SQL-authority membrane to the existing 0262
projection, 0263 recall/rehydration and 0269 one-shot composition.

The live path now:

- derives one opaque `sql_authority_ref` from the injected SQLite path and
  namespace;
- adds that scope to every live Qdrant upsert;
- rejects foreign and legacy unscoped hits before SQL rehydration;
- requires strict gRPC data intent on port 6334;
- keeps REST on a distinct administration endpoint, normally port 6333;
- requires matching scope proofs from 0262 and 0263 before 0269 closes.

## Required base

The repository must already contain:

- `0271-r2-qdrant_client_projection_executor`;
- `0271-r3-qdrant_client_live_projection_recall_binding`;
- `0271-r4-qdrant_sql_authority_scope_strict_grpc`.

The modified r3 files are locked to these exact preimages:

```text
src/context/production_prototype_smoke_composition_0269.py  24ec49c339157920fecb15424bde6f314e8fe7e7
tools/run_production_prototype_smoke_composition_0269.py    7bf86d3f4b5bf9149c137d5858abeedf1639baa4
tools/run_scheduler_managed_embedding_qdrant_projection_0262.py feb296831663d254f42e7fd474c1a15c65b400de
tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py a5180b15578bbeeb0518718c10b0f66c75dd49cc
```

The three CLI files retain mode `100755`.

## Boundaries

- no Scheduler loop change;
- no RuntimeManager, worker or orchestrator;
- no Qdrant daemon or collection administration;
- no implicit SQL write beyond the existing 0260 step;
- no SHM, RouteProxy or ControlProxy change;
- no API-key value serialization;
- old foreign/unscoped Qdrant points are ignored, not deleted.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Live smoke

Qdrant must already be running, and the collection must already exist with
vector dimension 384.

```bash
PYTHONPATH=src:. python \
  tools/run_production_prototype_smoke_composition_0269.py \
  --execute \
  --policy-decision-id policy:0271:scoped-live-grpc \
  --demo-eventbus \
  --live-qdrant \
  --qdrant-url http://127.0.0.1:6333 \
  --qdrant-collection autodoc_context_embeddings \
  --qdrant-timeout-seconds 10 \
  --qdrant-prefer-grpc \
  --qdrant-grpc-port 6334 \
  --strict-data-grpc \
  --sql-authority-namespace autodoc-local \
  --output .var/reports/production_prototype_smoke_composition_0269.json \
  --format summary
```

Expected high-level result:

```text
production_prototype_smoke_composition_valid=True
issues=0
qdrant_mode=live
steps=9/9
remote_mutation_allowed=False
services_started=False
```
