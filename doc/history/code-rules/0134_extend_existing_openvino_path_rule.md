# Code rule addendum — 0134 existing OpenVINO/E5 path

Before adding any new OpenVINO or E5 adapter, audit the existing inference package.

Preferred surfaces:

```text
reuse or extend src/inference/openvino_embedding_adapter.py
reuse or extend src/inference/e5_pipeline.py
reuse or extend src/inference/embedding_pipeline.py
reuse or extend src/inference/openvino_backend.py
reuse or extend src/inference/registry.py
```

`openvino` imports remain confined to `src/inference/openvino_runtime.py` unless a future code-rule update explicitly expands that boundary.

Do not import OpenVINO from Scheduler, Dispatcher, PolicyEngine, RouteProxy, or context contracts.

Do not create a parallel adapter such as:

```text
E5OpenVINOEmbeddingAdapter
NewOpenVINOEmbeddingAdapter
OpenVINOVectorIndexer
```

unless an audit documents a concrete gap in the existing stack and explains why extension is insufficient.

openvino imports remain confined to src/inference/openvino_runtime.py
