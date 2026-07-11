# Release 0272-r9 — ProjectV2 vector projection

This release opens the vector projection stage after the durable r8 SQL gate.
It introduces an immutable E5/Qdrant space profile, blocks incompatible
embeddings before Qdrant, and carries both `sql_ref` and
`embedding_profile_ref` in projection payloads.

The implementation reuses the existing 0261, 0262 and 0271 surfaces. It does
not introduce a second embedding engine, Qdrant authority, manager,
orchestrator, laboratory runtime or bus.
