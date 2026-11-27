# 0292 — Current architecture and Copilot routing context

## Intention
Reconcile the current architecture and the server-side Copilot routing-context specification against the actual Git branch state after 0288.

## Base
- Branch: `docs/unification-027x`
- Base commit: `56dc340a8f5c8b88295d35888b13a2d12e03c0cf`
- Parent history already includes 0288 at `74043d9795dad79adb6597eb81f46a26d33b67ef`.

## Scope
- Refresh the current-state entrypoint and documentation index.
- Add a consolidated architecture view.
- Specify the non-authoritative server routing context for Copilot.
- Preserve the distinction between ProjectV2 #2 query-only source and ProjectV2 #3 research/projection target.

## Explicit boundaries
- Documentation only; no runtime provider is claimed.
- Scheduler remains the sole orchestration/admission authority.
- SQL/PostgreSQL remains durable authority; Qdrant remains projection/recall.
- EventBus, PassiveSupervisor and VisPy remain observation-only.
- ControlProxy remains transport-only.
- 0288 remains contract-only; no OS collector or poller.
- No new manager, orchestrator, worker, queue, bus, registry or proxy.

## Validation
No tests executed for this documentation-only patch. Historical test results are not re-attributed to 0292.
