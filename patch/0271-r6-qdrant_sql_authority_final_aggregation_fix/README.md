# 0271-r6 — Qdrant SQL-authority final aggregation fix

## Purpose

Correct the final 0269 aggregation false negative observed after the scoped live
gRPC smoke completed all nine phases.

Both 0262 and 0263 reports already contained the same non-empty
`sql_authority_ref`, but the 0269 CLI `_load_report` allow-list did not extract
that key. The core therefore received two empty phase references and rejected
the otherwise valid 9/9 composition.

## Change

This patch modifies only the existing 0269 CLI adapter:

- extract `sql_authority_ref` as an immutable child-report reference;
- preserve the existing 0262/0263 equality gate in the core;
- publish the common value in final `references`;
- include it in the human-readable summary.

It adds focused tests and phase documentation. It does not modify 0262, 0263,
Qdrant IO, SQL IO, gRPC policy, SHM or Scheduler.

## Required base

The repository must already contain:

- `0271-r4-qdrant_sql_authority_scope_strict_grpc`;
- `0271-r5-qdrant_sql_authority_scope_live_binding`.

Expected preimage:

```text
tools/run_production_prototype_smoke_composition_0269.py
blob 3e04c8401a18f880649d35c3e9dd6f3459c69876
mode 100755
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Live smoke

```bash
PYTHONPATH=src:. python \
  tools/run_production_prototype_smoke_composition_0269.py \
  --execute \
  --policy-decision-id policy:0271:scoped-live-grpc-r6 \
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

Expected result includes:

```text
production_prototype_smoke_composition_valid=True
issues=0
qdrant_mode=live
steps=9/9
sql_authority_ref=sql-authority:sqlite:...
```
