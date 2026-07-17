# Changelog 0287-r7-r15-r3-r10

- Extended manual runtime configuration with physical collection, deferred alias,
  dense vector name and sparse vector name.
- Preserved legacy unnamed-vector readiness when the new names are absent.
- Added named dense+sparse Qdrant readiness validation.
- Added a dedicated qdrant-client collection-admin I/O membrane.
- Added preview-first collection planning with a stable digest.
- Added controlled physical collection and canonical payload-index creation.
- Explicitly excluded deletion, alias mutation and point writes.
- r10-r1: restored compatibility for existing direct `QdrantRuntimeSettings` callers.
