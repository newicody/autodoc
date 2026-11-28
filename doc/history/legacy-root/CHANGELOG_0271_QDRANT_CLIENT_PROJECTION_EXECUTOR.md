# Changelog 0271-r2

- add the concrete `QdrantClientProjectionExecutor` for the existing protocol;
- select and pin official `qdrant-client==1.18.0` after the r1 reuse audit;
- add deterministic Qdrant UUID mapping while preserving Autodoc point refs;
- require explicit write/search effect gates;
- preserve `payload.sql_ref` and fail closed on invalid recall payloads;
- add typed SDK failure wrapping and dependency readiness checking;
- keep Scheduler, services and SHM unchanged.
