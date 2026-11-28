# Code rule addendum — 0138 OpenVINO/E5 live smoke existing path

Before running an OpenVINO/E5 live smoke, verify the existing surfaces are present and avoid creating a new adapter.

The live smoke must:

```text
reuse tools/embed_e5.py
reuse src/inference/openvino_embedding_adapter.py
reuse src/inference/openvino_runtime.py
dry-run must remain the default
```

do not import OpenVINO from Scheduler, Dispatcher, PolicyEngine, RouteProxy, Qdrant, or context contracts.

Forbidden new wheels:

```text
SchedulerOpenVINORunner
VectorOpenVINOEmbeddingAdapter
RouteProxyOpenVINOWorker
QdrantOpenVINOFusionAdapter
```
