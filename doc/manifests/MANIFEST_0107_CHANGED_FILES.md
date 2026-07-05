# Manifest — 0107 ControlProxy graph root alignment

0107 is a documentation, DOT and rule-test patch. It does not add runtime code.

## Added files

```text
PHASE0107_TEST_REPORT.md
doc/CHANGELOG_0107_CONTROLPROXY_GRAPH_ROOT_ALIGNMENT.md
doc/architecture/CONTROLPROXY_GRAPH_ROOT_ALIGNMENT_0107.md
doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0107.md
doc/docs/architecture/runtime/97_controlproxy_root_alignment.dot
doc/manifests/MANIFEST_0107_CHANGED_FILES.md
tests/rules/test_controlproxy_graph_root_alignment_0107_rule.py
```

## Kernel guardrails

0107 does not modify Scheduler, Dispatcher, PolicyEngine, PriorityQueue,
EventBus, Component contracts, ContextGate, Qdrant, RouteRuntimeManager or any
runtime module.

## Graph guardrails

```text
ROOT_GRAPH: doc/docs/architecture/00_global.dot
root-attached runtime overlay
not an isolated graph
Dispatcher = EventType -> Handler only
Route mmap/eventfd = data plane, not EventBus
```
