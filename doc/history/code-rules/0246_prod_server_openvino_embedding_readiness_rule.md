# Code rule 0246 - OpenVINO embedding readiness

Patch 0246 may validate OpenVINO embedding readiness only.

Required:

```text
OpenVINO is explicit before Qdrant projection
multilingual-e5-small shape is locked
dimension = 384
normalized = true
distance = cosine
query prefix = query:
passage prefix = passage:
```

Forbidden in this phase:

```text
importing OpenVINO
importing Transformers
reading model files
loading a model
running inference
writing PostgreSQL
creating/upserting Qdrant collections or points
publishing EventBus events
calling GitHub API
adding non-stdlib dependencies
```
