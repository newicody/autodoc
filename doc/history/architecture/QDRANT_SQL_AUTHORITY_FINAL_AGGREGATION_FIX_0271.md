# 0271-r6 — Qdrant SQL-authority final aggregation fix

## Scope

This is an aggregation-only correction for the existing 0269 CLI adapter.
Reports 0262 and 0263 already publish one matching `sql_authority_ref`, and the
0269 core already validates both phase-local references. The CLI report loader
was not extracting that key, so the final gate observed two empty values.

The correction:

- extracts `sql_authority_ref` from each child report;
- preserves the existing phase-local equality gate;
- lets the common value flow into final `references`;
- shows the common authority in the summary.

## Boundaries

- no Qdrant call;
- no SQL write;
- no SHM change;
- no Scheduler loop change;
- no change to 0262, 0263, the Qdrant executor, or transport policy;
- no new manager, orchestrator, adapter, handler, worker, or daemon.

The live evidence remains owned by the existing reports. This patch only fixes
how the final one-shot composition reads and displays that evidence.
