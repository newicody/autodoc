# Changelog 0264 - Scheduler-managed closed ResultFrame

## r1

Adds a non-runtime closed ResultFrame composer for the 0260-0263 path.

The composer reads reports, validates continuity of `sql_ref` and
`embedding_ref`, and emits a serialisable frame.
