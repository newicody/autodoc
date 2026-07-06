# Code rule addendum — 0142 machine vector handoff

Before adding any strict vector-indexing smoke or runner, machine-readable vector handoff must use tools/embed_e5.py --format json --full-vector.

Qdrant smoke may consume that file through --vector-json.

Rules:

- never parse values_preview as a full vector
- do not create LocalVectorIndexingOrchestrator
- do not create VectorOpenVINOEmbeddingAdapter
- do not create VectorQdrantProjectionAdapter
- keep OpenVINO behind the existing E5/OpenVINO CLI and runtime boundary
- keep Qdrant behind the existing Qdrant projection smoke tool and adapter contracts
- keep Scheduler and RouteProxy outside OpenVINO and Qdrant
