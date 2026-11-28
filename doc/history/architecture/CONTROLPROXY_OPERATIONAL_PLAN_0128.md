# 0128 operational note — Vector indexing jobs

0128 keeps ControlProxy and route runtime as data-plane infrastructure.  It does not promote ControlProxy to policy or orchestration authority.

The Scheduler remains the orchestration authority.  Vector indexing work is represented as immutable command/job data, while `/dev/shm` route frames are used as the multitask data-plane interface and future grid seam.

```text
Scheduler command
-> vector indexing route frames under /dev/shm
-> E5/OpenVINO adapter later
-> Qdrant projection adapter later
-> EventBus observation facts
-> SQL durable refs
```

No kernel file is modified in 0128.
