# Manifest 0098 — ControlProxy dispatch filtering envelope

Changed files:

```text
src/runtime/route_dispatch_filter_envelope.py
tests/runtime/test_route_dispatch_filter_envelope.py
tests/rules/test_route_dispatch_filter_envelope_rule.py
doc/architecture/CONTROLPROXY_DISPATCH_FILTERING_0098.md
doc/architecture/RUNTIME_CONTROLFS_SHM_CLUSTER_FABRIC_GRAPH_0098.dot
doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0098.md
doc/manifests/MANIFEST_0098_CHANGED_FILES.md
PHASE0098_TEST_REPORT.md
```

0098 adds a route dispatch-filter envelope and updates architecture documents and
DOT graph structure. It does not change Scheduler, PriorityQueue, Dispatcher, or
Component contract files.
