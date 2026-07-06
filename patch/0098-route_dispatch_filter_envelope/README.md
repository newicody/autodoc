# 0098 — Route dispatch filter envelope

This patch adapts the ControlProxy/ControlFS policy-zone wording after the graph
review. The security-shaped route envelope is now described as policy/zone
dispatch filtering: it filters coherent dispatch into ControlProxy/ControlFS but
does not make ControlProxy a security policy authority.

## Scope

Adds:

- `src/runtime/route_dispatch_filter_envelope.py`
- `tests/runtime/test_route_dispatch_filter_envelope.py`
- `tests/rules/test_route_dispatch_filter_envelope_rule.py`
- `doc/architecture/CONTROLPROXY_DISPATCH_FILTERING_0098.md`
- `doc/architecture/RUNTIME_CONTROLFS_SHM_CLUSTER_FABRIC_GRAPH_0098.dot`
- `doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0098.md`
- `doc/manifests/MANIFEST_0098_CHANGED_FILES.md`
- `PHASE0098_TEST_REPORT.md`

## Boundaries

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher, or Component tick contract modification.
- ControlProxy does not decide security policy.
- Scheduler/policy/zone remain the authority.
- Existing event.bus/context.bus remain observation surfaces.
- No live mmap resize.
- Not /dev/shm-only.
- No NetworkBridge or HardwareBridge implementation.
- No Qdrant, LLM, or OpenVINO path.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_dispatch_filter_envelope.py
PYTHONPATH=src:. pytest -q tests/rules/test_route_dispatch_filter_envelope_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
