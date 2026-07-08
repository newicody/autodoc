# 0234 — All-surfaces passive supervisor smoke

## Objective

Patch 0234 adds a functional smoke that verifies the passive supervision chain
for every planned event family without adding a new runtime component.

The covered path is:

```text
Scheduler / RouteProxy / ControlProxy / SHM / Policy / GitHub artifact / SourceCandidate / SQL / Qdrant / Rehydration / Pushback
  -> existing EventBus event contract
  -> PassiveSupervisorSink
  -> CellularState
  -> snapshot optionnel
  -> audit/replay optionnel
```

## Authority boundary

The smoke is downstream-only. It does not:

```text
create a new EventBus
call Scheduler.run()
control RouteProxy or ControlProxy
read or mutate raw SHM
make a policy decision
call GitHub
promote SourceCandidate
read or write SQL
query or upsert Qdrant
execute rehydration
execute pushback
introduce non-stdlib dependencies
```

## Why this patch exists

Patches 0230 through 0233 connected the passive supervisor to the canonical
families of events. Patch 0234 proves that those families can coexist in one
single snapshot/audit smoke before any visual layer or deeper runtime wiring is
introduced.

## Outputs

The smoke writes a JSON report containing:

```text
all_surfaces_passive_supervisor_smoke_passed
expected_cell_kinds
observed_cell_kinds
missing_cell_kinds
event_count
snapshot
authority_boundary
```

An audit JSONL output is optional and is used only for audit/replay/testing.
It is not the runtime path.
