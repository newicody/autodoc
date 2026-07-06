# 0134 operational note — Existing OpenVINO path

0134 does not change RouteProxy or Scheduler. It locks the inference side before wiring vector jobs.

Operational direction:

```text
Scheduler vector indexing command
-> existing handler path
-> RouteProxy /dev/shm frames
-> existing OpenVINO/E5 embedding membrane
-> Qdrant projection adapter later
```

No OpenVINO import is introduced outside `src/inference/openvino_runtime.py`.
