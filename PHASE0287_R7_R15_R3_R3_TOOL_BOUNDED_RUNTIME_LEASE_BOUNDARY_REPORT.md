# Phase 0287-r7-r15-r3-r3 — tool-bounded runtime lease boundary

## Decision

The first live imported-run preview cannot safely be composed by registering
runtime ports in one long-lived server process and consuming them from a
separate CLI process.  The provider registry introduced by r15-r3-r2 is
process-local by design.  Treating it as an interprocess bootstrap would create
an invalid wiring claim.

The imported-run CLI already owns a valid Scheduler lifecycle mode named
`tool-bounded`.  This patch therefore closes the missing ownership boundary
before any live PostgreSQL, Qdrant or OpenVINO composition is introduced.

## Implemented boundary

A runtime factory may now return either:

1. legacy `ImportedActionsRuntimePorts`; or
2. `ImportedActionsRuntimeLease`, which owns the same validated ports plus
   synchronous close hooks.

The lease:

- is tied to the process that created it;
- accepts close hooks only for `tool-bounded` runtimes;
- closes hooks in reverse acquisition order;
- executes every hook even if one hook fails;
- closes exactly once and returns a replay receipt on later calls;
- exposes a serializable readback without exposing callback objects;
- keeps legacy direct-port factories compatible through a no-op lease.

## CLI integration

`tools/run_love_actions_closed_loop_0287.py` now acquires a lease from the
runtime factory and passes it into the existing r14 Scheduler lifecycle.

For `tool-bounded` runtimes the order is:

```text
r14 completion or failure
→ Scheduler shutdown / task completion
→ runtime close hooks in reverse order
→ lease readback
→ publication preview construction
```

If the injected Scheduler fails before r14 completes, r14 is cancelled and the
lease is still closed.  If command construction fails after factory creation,
the outer guard closes the lease as well.

For `externally-managed` runtimes the CLI neither starts/stops the Scheduler nor
closes externally owned resources.

The final preview JSON gains:

```text
_r15_runtime_lease
```

containing owner, process, Scheduler lifecycle, hook references, close status
and the exact close receipt.

## Boundaries preserved

This patch does not:

- construct a Scheduler or Dispatcher;
- open PostgreSQL;
- instantiate Qdrant;
- compile or execute OpenVINO;
- create a laboratory or manager;
- perform a remote mutation;
- claim that a live preview has already run.

SQL remains the durable authority.  Qdrant remains a projection/recall surface
for references.  E5 remains fixed at 384 dimensions by the existing runtime
attestation.

## Roadmap adjustment

The originally planned live composer is moved to the next sub-unit:

```text
0287-r7-r15-r3-r3-r1
canonical tool-bounded live runtime composer and first preview
```

That unit may now safely acquire PostgreSQL, Qdrant and OpenVINO in the CLI
process and register deterministic close hooks without leaking resources or
pretending that a process-local registry is shared between processes.
