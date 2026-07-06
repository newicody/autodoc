# 0130 — RouteProxy runtime minimal

0130 starts the first live local data-plane path after the 0129 RouteProxy flow-control contracts.

RouteProxy runtime is a data-plane executor, not an orchestrator. Scheduler remains the orchestrator. Do not modify Scheduler.run() in 0130.

## What this patch adds

```text
prepare a RouteProxy runtime root
create frames/meta/facts directories
request a writer permit
write one route frame atomically
read one route frame
mark one route frame stale when context generation advances
persist observation-ready facts
```

## Boundary lock

- RouteProxy runtime is a data-plane executor, not an orchestrator.
- Scheduler remains the orchestrator.
- Do not modify Scheduler.run() in 0130.
- No mount table scan is allowed.
- `/dev/shm` remains the default local multitask route interface and future grid seam.
- Test roots must explicitly set `require_dev_shm=False` and `allow_test_root=True`.
- EventBus receives observation-ready facts, not payload commands.
- SQLContextStore remains durable authority.
- E5/OpenVINO and Qdrant are not touched by 0130.
- GitHub exchanges artifacts only and is not part of this runtime.

## Why no mount table scan

Older route runtime validation could fail by resolving unrelated protected mount points such as debug tracing paths. 0130 does not scan `/proc/mounts` and does not resolve global mount entries. It validates only the configured route root and its direct runtime directories.

## Runtime shape

```text
RouteProxyRuntimePolicy
-> prepare_route_proxy_runtime()
-> RouteProxyRuntimeState
-> request_writer_permit()
-> write_route_frame()
-> read_route_frame()
-> mark_route_frame_stale()
-> list_observation_facts()
```

## Documentation update status

documentation architecture is updated in this patch through:

```text
doc/architecture/ROUTE_PROXY_RUNTIME_MINIMAL_0130.md
doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0130.md
doc/docs/architecture/runtime/130_route_proxy_runtime_minimal.dot
doc/code-rules/0130_route_proxy_runtime_rule.md
```

The code_rule supplement for RouteProxy runtime membrane is added as a dedicated rule file. It extends the principal rule set without rewriting the principal file blindly.

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
code_rule_update_kind: supplemental_rule_file
live_path_status: first_runtime_step
live_path_uses_real_backend: local_filesystem_only
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
