# 0139 operational note — Qdrant projection live smoke

0139 keeps Qdrant outside Scheduler and RouteProxy.  The Qdrant projection live smoke is an operator test through `src/inference/qdrant_projection_adapter.py` only.

```text
text/vector payload
-> existing Qdrant projection membrane
-> Qdrant projection/recall index
-> sql_ref preserved
-> SQLContextStore remains durable authority
```

If the existing Qdrant adapter has no executable smoke entrypoint, extend that existing file in the next patch. Do not create a parallel adapter.
