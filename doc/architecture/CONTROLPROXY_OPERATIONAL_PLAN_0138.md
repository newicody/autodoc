# 0138 — ControlProxy operational plan update

0138 does not change ControlProxy or RouteProxy runtime behavior.

It verifies the OpenVINO/E5 side of the future vector-indexing path using the existing operator CLI and inference membrane:

```text
operator command
-> tools/embed_e5.py
-> src/inference/openvino_embedding_adapter.py
-> src/inference/openvino_runtime.py
-> E5 vector output
```

RouteProxy, Scheduler, Qdrant, SQL, and EventBus remain outside this smoke step.
