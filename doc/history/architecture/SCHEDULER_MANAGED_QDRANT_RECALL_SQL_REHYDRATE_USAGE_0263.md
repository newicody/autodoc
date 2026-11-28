# Scheduler-managed Qdrant recall to SQL rehydrate usage - 0263

## Intent

0263 composes the next production prototype step:

```text
Qdrant recall -> sql_ref -> SQL rehydrate
```

Qdrant is recall only and carries refs. SQL remains the durable authority for
the content body, title, metadata, and parent references.

## Boundary

Scheduler does not start Qdrant. Qdrant remains an external service used by an
Autodoc recall object through an injected executor.

OpenVINO is not executed in 0263. The input embedding report must already exist.

No RuntimeManager is introduced. Scheduler.run is not modified.

## Existing surfaces reused

```text
QdrantRecallQuery
QdrantRecallHit
QdrantRecallResult
unique_sql_context_refs_from_recall
DbApiSqlContextStore.get_record / SQLiteSqlContextStore.get_record
```

Dry-run validates the recall plan. Execute requires a `policy_decision_id` and an
injected executor. The smoke executor returns reference-only hits derived from
the 0262 projection report.

## Next step

0264 can compose the closed ResultFrame from SQL write, OpenVINO embedding,
Qdrant projection, Qdrant recall, and SQL rehydrate.
