# 0127 — Vector collection registry

Added a local/importable registry contract for Qdrant role collections.

- Adds `src/context/vector_collection_registry.py`.
- Adds runtime and rule tests.
- Documents one Qdrant instance with multiple role-oriented collections.
- Keeps Scheduler as orchestrator, SQL as durable authority, E5/OpenVINO as embedding-only adapter, Qdrant as projection/recall only, GitHub as artifact exchange only.
