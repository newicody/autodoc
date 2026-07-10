# Scheduler-managed sql_ref to OpenVINO embedding usage - 0261

## Intent

0261 composes the next production prototype step:

```text
sql_ref -> SQL rehydrate -> OpenVINO/E5 passage embedding
```

The `sql_ref` comes from the real 0260 SQL controlled write. SQL remains the
durable authority and the record body/title are rehydrated with
`DbApiSqlContextStore.get_record`.

## Boundary

Scheduler does not start OpenVINO. OpenVINO remains an explicit runtime/model
surface used by an Autodoc object.

Qdrant is not involved in 0261.

No RuntimeManager is introduced. Scheduler.run is not modified.

## Existing surfaces reused

```text
DbApiSqlContextStore.get_record
build_multilingual_e5_small_pipeline
tools/embed_e5.py -> inference.e5_cli -> e5_pipeline
```

Dry-run validates SQL rehydration and the E5 passage text. Execute requires a
`policy_decision_id` and then calls the existing OpenVINO/E5 pipeline, unless a
demo embedder is injected for tests.

## Next step

0262 can project the embedding toward Qdrant with `payload.sql_ref`, while SQL
remains the durable authority.
