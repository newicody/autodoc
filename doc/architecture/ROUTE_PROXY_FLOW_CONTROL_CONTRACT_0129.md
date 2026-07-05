# 0129 — RouteProxy flow-control contract

RouteProxy is fast data-plane flow control, not an orchestrator.

0129 introduces a pure contract layer for protecting `/dev/shm` route zones when many local workers and specialists exchange frames concurrently.  It does not create a daemon, watcher, GitHub client, Qdrant client, OpenVINO runtime, PostgreSQL driver, or live EventBus subscription.

## Locked boundary

- Scheduler remains the orchestrator.
- RouteProxy is fast data-plane flow control, not an orchestrator.
- /dev/shm route zones are a multitask interface and future grid seam.
- RouteProxy can reserve, block, stale, and reprioritize route zones quickly.
- EventBus receives observation facts and statistics, not payload commands.
- RouteProxy registry snapshots are runtime mirrors, not durable authority.
- SQLContextStore remains durable context authority.
- E5/OpenVINO remains embedding only behind adapter.
- Qdrant remains projection and recall only.
- GitHub exchanges artifacts only.
- Do not modify Scheduler.run() in 0129.

## Why the proxy exists

The deliberation loop can create several concurrent workers: thermal, material, safety, bias review, synthesis, vector indexing, and other specialists.  `/dev/shm` is a fast local interface for that multitask exchange and a future grid seam, but writers need a fast guard so stale context or lower-priority work does not keep writing into zones that the Scheduler has already superseded.

RouteProxy therefore applies quick route-level control:

```text
Scheduler decision
-> RouteProxy lease / writer permit / generation fence
-> /dev/shm route zone
-> worker reads or writes if permit is valid
-> EventBus observation fact
-> SQL durable state later
```

## What RouteProxy may do

```text
reserve a route zone for one owner
block a writer while a context generation changes
mark old route frames stale
apply a priority hint decided by Scheduler
emit route pressure signals
publish runtime registry snapshots for observation
mirror collection/route registries for fast lookup
```

## What RouteProxy must not do

```text
choose which specialist is right
replace Scheduler or PolicyEngine
make business decisions
become SQL authority
put heavy payloads on EventBus
turn GitHub into an internal work bus
```

## Runtime mirrors

RouteProxy may hold a fast mirror of active routes, leases, specialists, context generation, and registry refs.  That mirror is not the truth.  The truth remains SQL plus declared registries and Scheduler/Policy decisions.

## Phase status

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0129 adds pure immutable contracts for RouteProxy flow control and follows existing data-plane/kernel boundaries.
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
