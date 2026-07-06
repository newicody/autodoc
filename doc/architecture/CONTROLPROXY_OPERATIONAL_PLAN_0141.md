# 0141 operational note — local vector indexing smoke

0141 is an operator smoke chain:

```text
tools/run_local_vector_indexing_live_smoke.py
-> tools/run_openvino_e5_live_smoke.py
-> tools/run_qdrant_projection_live_smoke.py
```

It proves the local operator surfaces can run together.  It does not make Scheduler call OpenVINO or Qdrant.  It does not make RouteProxy call OpenVINO or Qdrant.  It does not replace SQL authority with Qdrant.

The next functional boundary is a machine-readable vector handoff from the existing E5/OpenVINO membrane, if full end-to-end vector transfer is required without deterministic projection probes.
