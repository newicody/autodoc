# Code rule 0247 - Qdrant collection readiness

Patch 0247 may validate Qdrant collection readiness only.

Required:

```text
Qdrant readiness is aligned with OpenVINO readiness
vector dimension matches OpenVINO dimension
Qdrant distance matches OpenVINO expected distance
required payload includes sql_ref
required payload includes model_id/embedding_version/content_hash
```

Forbidden in this phase:

```text
calling Qdrant API
creating Qdrant collections
upserting Qdrant points
running OpenVINO inference
writing PostgreSQL
publishing EventBus events
calling GitHub API
adding non-stdlib dependencies
```
