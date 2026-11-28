# Changelog 0135 — vector indexing through existing OpenVINO path

Added tests and documentation proving that `VectorEmbeddingJob` can feed the existing OpenVINO/E5 embedding contracts without creating another adapter.

No production runtime, Scheduler, RouteProxy, Qdrant, or OpenVINO import boundary was changed.
