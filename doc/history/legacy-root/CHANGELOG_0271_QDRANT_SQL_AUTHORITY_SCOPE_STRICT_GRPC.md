# Changelog — 0271-r4 SQL-authority scope and strict gRPC

- Added a protocol-preserving SQL-authority scope wrapper for Qdrant executors.
- Added opaque SQLite authority-ref derivation without path disclosure.
- Added projection payload enrichment and pre-rehydration recall filtering.
- Added a strict gRPC transport policy separating REST administration from data.
- Added a readiness-only CLI with no network, Qdrant, SQL or SHM effects.
- Deferred integration into 0262/0263/0269 to 0271-r5.
