# ControlProxy operational plan — 0100 correction

## Stop adding parallel primitives

The next phase must avoid adding another independent helper around routes.
The route stack now needs a single coordinator boundary that explains how the existing active-route handshake lane and the generation/runtime lane meet.

## Current lanes

- Lane A: `0081/0084/0085/0086/0088`, active route materialization and Scheduler-facing handshake.
- Lane B: `0091-r2/0092/0094/0095/0096`, generation table, lifecycle, lock, and runtime placement.

Both lanes are useful, but they are not yet one operational path.
The graph must represent that honestly.

## 0101 target

Create a small importable coordinator that receives an already authorized Scheduler route payload and chooses between:

- reuse active route through the existing handshake path;
- create first generation through the locked materializer;
- create next generation through the locked materializer;
- leave activation/drain policy explicit and testable.

The coordinator must be behind the Dispatcher handler boundary.
It must not modify `Scheduler.run()`, `PriorityQueue`, `Dispatcher`, or the Component tick/reply contract.

## Vocabulary update

Replace future documentation language that says ControlProxy "applies security policy" with:

```text
ControlProxy applies policy/zone dispatch filtering and runtime sizing constraints for already-decided route work.
```

The `ControlProxyZonePolicy` name is legacy and should later become a sizing/profile object, not a second `PolicyEngine`.
