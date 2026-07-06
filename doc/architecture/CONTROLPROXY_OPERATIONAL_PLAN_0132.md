# 0132 operational note — integration audit before next runtime work

0132 does not add ControlProxy behavior.  It adds an audit gate.

Before extending RouteProxy, Scheduler handlers, fake specialists, OpenVINO, or Qdrant, the next patch must inventory existing surfaces and choose reuse/extend/modify/create-with-gap.

For the current local line, the known surfaces are:

```text
src/runtime/route_proxy_runtime_minimal.py
src/runtime/scheduler_route_handler_minimal.py
```

So the next route/handler work should extend those modules or prove that the real repository already has a better target.
