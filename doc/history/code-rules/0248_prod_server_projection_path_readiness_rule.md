# Code rule 0248 - projection path readiness

Patch 0248 may compose SQL/OpenVINO/Qdrant readiness only.

Required:

```text
SQL record -> OpenVINO embedding -> Qdrant point path is explicit
Qdrant payload keeps sql_ref
OpenVINO dimension matches Qdrant dimension
Qdrant remains projection/recall only
SQL remains durable authority
```

Forbidden in this phase:

```text
opening PostgreSQL connections
executing SQL
running OpenVINO inference
calling Qdrant API
creating Qdrant collections
writing Qdrant points
publishing EventBus events
calling GitHub API
adding non-stdlib dependencies
```
