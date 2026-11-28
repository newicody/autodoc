# Changelog 0284-r6 — portable specialist real-memory closure

- Added a preview-first composition over the existing 0284-r5 specialist path.
- Reused the existing 0283 scoped Qdrant executor factory twice: projection-only
  and recall-only.
- Reused the existing 0261 real passage/query OpenVINO E5 path.
- Locked multilingual-E5-small vectors to exactly 384 dimensions.
- Verified that Qdrant returns the specialist `sql_ref` under the existing reference-only boundary and SQL rehydrates it.
- Required the existing concrete `DbApiSqlContextStore` in execute mode.
- Locked one policy decision, collection, transport and SQL-authority scope across projection and recall.
- Required explicit real-memory and persistent-point authorizations.
- Added no Scheduler, laboratory, provider, executor, transport, bus or manager.
- Added no automatic SQL or Qdrant cleanup.
