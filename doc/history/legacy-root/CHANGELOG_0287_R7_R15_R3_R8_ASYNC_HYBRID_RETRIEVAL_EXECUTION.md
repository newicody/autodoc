# Changelog 0287-r7-r15-r3-r8

- Added an async entry point for the existing hybrid retrieval composition.
- Awaited the injected dense E5 query adapter exactly once.
- Reused `execute_hybrid_retrieval()` for all validation and rehydration.
- Added a one-shot precomputed embedding bridge.
- Added non-secret execution evidence without raw vectors.
- Deferred real Qdrant dense/sparse adaptation to r15-r3-r9.
