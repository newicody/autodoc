# Live runtime composer reuse audit — 0287-r7-r15-r3-r5

```text
existing Scheduler + Dispatcher
              │ reuse
              ▼
       tool-bounded composer
        ├─ PostgreSQL DB-API authority     missing live connection + seed
        ├─ OpenVINO E5 pipeline            reusable; async adapter missing
        ├─ Qdrant client executor          reusable; hybrid adapters missing
        ├─ love analysis projection        contract exists; adapter missing
        └─ native/collaborative handlers   reusable
              │
              ▼
 ImportedActionsRuntimePorts + Lease
```

The composer is a leaf composition boundary in the CLI process.  It must not be
placed in the domain contracts and must not create a second orchestration path.
