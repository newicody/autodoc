# 0144 operational plan — vector indexing result frame

0144 keeps ControlProxy/RouteProxy as data-plane frame IO. It does not add a daemon or new worker.

```text
request frame
-> local vector indexing smoke
-> result frame
```

The result frame is written back through the existing Scheduler route handler and existing RouteProxyRuntime. SQL remains durable authority; Qdrant remains projection/recall; OpenVINO remains behind the inference membrane.
