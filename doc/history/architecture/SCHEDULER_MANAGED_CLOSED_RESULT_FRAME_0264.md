# Scheduler-managed closed ResultFrame - 0264

## Intent

0264 composes a closed ResultFrame from the reports produced by the previous
controlled steps:

```text
0260 -> 0261 -> 0262 -> 0263
```

It verifies that the same `sql_ref` flows through SQL write, SQL rehydrate,
OpenVINO/E5 embedding, Qdrant projection, Qdrant recall, and final SQL
rehydration.

## Boundary

0264 does not execute SQL, OpenVINO, or Qdrant. It reads existing JSON reports
and emits a serialisable frame.

SQL remains the durable authority. Qdrant remains projection/recall only and
carries references. OpenVINO has already been executed by 0261.

Scheduler does not start PostgreSQL, OpenVINO, or Qdrant. No RuntimeManager is
introduced. Scheduler.run is not modified.

## Output

The frame contains:

```text
schema
sql_ref
embedding_ref
projection_point_count
recall_hit_count
hydrated_count
missing_count
hydrated_records
trace.0260/0261/0262/0263
```

## Next step

0265 can attach EventBus observation-only facts around the closed frame without
turning events into commands.
