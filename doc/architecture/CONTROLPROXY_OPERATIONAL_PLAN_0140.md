# 0140 operational plan — Qdrant live smoke stays outside ControlProxy

Qdrant live REST execution is an operator smoke only. ControlProxy/RouteProxy remains data-plane flow control for `/dev/shm` and does not import Qdrant.

```text
operator smoke
-> existing Qdrant projection contracts
-> local Qdrant REST
-> sql_ref payload
```

Scheduler and RouteProxy stay outside Qdrant.
