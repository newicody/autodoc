# Tool-bounded installed runtime composer

```text
installed runtime factory
        |
        v
tool-bounded provider
        |
        +-- canonical Scheduler stack
        +-- PostgreSQL authority binding
        +-- OpenVINO multilingual-E5 pipeline
        +-- qdrant-client executor
        +-- live projection adapter
        +-- async query embedder
        +-- dense/sparse query adapter
        +-- canonical named-vector profile
        |
        v
ImportedActionsRuntimeLease
        |
        +-- ports
        +-- close Qdrant
        +-- close PostgreSQL
```

The provider does not run the Scheduler. The existing CLI owns its asynchronous
run/shutdown lifecycle. No laboratory manager or parallel orchestrator exists.
