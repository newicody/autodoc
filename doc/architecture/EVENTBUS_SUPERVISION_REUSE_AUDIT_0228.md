# 0228 — EventBus supervision reuse audit

## Purpose

This phase is the first functional step after the written functional resumption gate.
It does not implement the runtime sink yet. It adds a read-only audit tool that scans
existing repository surfaces before any EventBus supervision runtime code is added.

The target architecture remains:

```text
Scheduler / RouteProxy / ControlProxy / SHM / Policy / Data surfaces
  -> EventBus
  -> PassiveSupervisorSink
  -> CellularState
```

`EventBus -> PassiveSupervisorSink -> CellularState` is the only intended live path
for passive supervision. `snapshot is optional` and `events.jsonl is optional`.
They are audit, replay, debug, inspection, or view outputs, not the live runtime spine.

## Why this phase exists

The project rule requires auditing and reusing existing code before adding a new
runtime, handler, adapter, module, or backend. The next implementation must not add
a parallel bus, a status-file bridge, or a second supervisor if existing surfaces can
be reused.

This audit makes the next implementation accountable by reporting evidence for:

```text
EventBus / publish / subscribe / emit / BusEvent
Scheduler / Scheduler.run
passive bus supervisor / CellularState / cellular snapshot
RouteProxy / ControlProxy / SHM / Policy
GitHub / SourceCandidate / sql_ref / qdrant_ref / rehydration / pushback
```

## Scheduler boundary

Scheduler remains the upstream orchestration authority. The supervisor may observe
Scheduler events carried by the EventBus, but it must not call `Scheduler.run()`, wrap
it, dispatch handlers, or decide execution order.

## Supervisor boundary

The supervisor remains downstream-only. It must not control RouteProxy or
ControlProxy, mutate SHM, decide policy, write SQL, write Qdrant, mutate GitHub,
or execute rehydration/pushback.

## Audit tool

The added tool is:

```text
tools/audit_eventbus_supervision_reuse_0228.py
```

It scans text files under `src`, `tools`, `doc`, and `tests` by default and writes a
JSON report when requested. It does not import runtime modules and has no runtime
side effects.

Example:

```bash
python tools/audit_eventbus_supervision_reuse_0228.py \
  --output .var/reports/eventbus_supervision_reuse_0228.json \
  --format summary
```

The report is intended to guide the next functional patch:

```text
reuse existing EventBus if present
reuse existing passive supervisor/cellular state if present
keep Scheduler upstream-only
keep snapshot/audit optional
avoid a new bridge unless the audit proves no reusable surface exists
```

## Functional resumption gate

A future runtime patch may proceed only after reviewing the audit report and making a
clear reuse decision. If existing EventBus or passive-supervision surfaces are found,
the implementation must extend them rather than create parallel infrastructure.
