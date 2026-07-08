# Changelog 0220 - Passive Bus Supervisor Cellular Snapshot

## Added

- Added `src/context/passive_bus_supervisor_cellular_snapshot.py`.
- Added `tools/run_passive_bus_supervisor_cellular_snapshot_0220.py`.
- Added focused context, tool, and rule tests.
- Added passive bus supervisor architecture documentation.
- Added DOT graph for the observation flow.
- Added manifest and phase test report for traceability.

## Boundary

The 0220 surface is:

- observation-only
- stdlib-only
- additive
- deterministic
- JSON-serializable

It does not:

- call GitHub
- call network APIs
- download artifacts
- mutate GitHub Projects
- call `Scheduler.run`
- write SQL
- write Qdrant
- control RouteProxy or ControlProxy
- require VisPy

VisPy is not introduced by this patch. It remains a future optional read-only
view over the emitted snapshot.

## Validation Note

This patch was prepared in a sandbox where the Autodoc checkout was not mounted
and GitHub access was blocked for local clone. Validation must be run in the real
repository through the patch queue.

## Fixed in 0220-r1

- Fixed direct CLI execution by inserting the repository root into `sys.path`
  before importing `src.context.passive_bus_supervisor_cellular_snapshot`.
- Kept the passive supervisor authority boundary unchanged.
