# 0145 operational plan — local artifact vector indexing runner

0145 wraps the existing Scheduler/RouteProxy/vector smoke with a local artifact envelope.

```text
local artifact input
-> existing Scheduler vector indexing smoke
-> existing RouteProxyRuntime frames
-> existing OpenVINO/Qdrant smoke tools
-> local artifact report
```

It does not move OpenVINO or Qdrant into Scheduler or RouteProxy. The runner is an operator surface only.
