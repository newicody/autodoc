# 0284-r9 — Specialists/laboratories live-path evidence

## Purpose

Phase 0284-r8 proved that all required implementation surfaces exist, but kept
the phase in `transition` until one correlated real run supplied operational
evidence. Phase r9 adds that evidence boundary without creating a second
execution path.

## Reuse decision

The patch reuses:

- `ProjectsCopilotSpecialistIntegratedSmokeResult.to_mapping()` from 0284-r7;
- `Phase0284OperationalEvidence` from 0284-r8;
- `audit_specialists_laboratories_chain_closure()` from 0284-r8;
- the existing Scheduler, SQL, OpenVINO, Qdrant and GitHub adapters indirectly
  through the result already produced by r7.

No provider, Scheduler, queue, EventBus, laboratory manager, transport or
backend adapter is added.

## Flow

```text
explicitly authorised 0284-r7 real run
  -> stable JSON result
  -> thin local IO adapter
  -> immutable r9 evidence command
  -> pure correlation and invariant verification
  -> Phase0284OperationalEvidence
  -> existing r8 closure audit
  -> deterministic evidence report + SHA-256 digests
```

## Correlation requirements

One green envelope requires the same:

- GitHub repository and Actions run id;
- policy decision across GitHub, SQL and Qdrant configuration;
- authoritative SourceCandidate;
- durable `sql_ref` in memory and publication preview;
- passage/query embedding references;
- exact Qdrant vector dimension `384`.

It also requires a completed existing-Scheduler path, real SQL authority, real
OpenVINO E5, real Qdrant projection and reference-only recall, SQL rehydration,
portable identity preservation, hint-only Copilot context, and ready but
unexecuted publication/ProjectV2 plans.

## Effect boundary

The r9 use-case performs no IO. The CLI reads an existing JSON result and the
repository source files, then optionally writes one report atomically. It has no
`--execute` option and performs no network or backend call.

## Closure semantics

- `green`: evidence and repository audit close 0284;
- `transition`: implementation remains valid but evidence is incomplete;
- `red`: repository surface or safety invariant is invalid.

A green unit fixture validates the contract only. Operational closure is
claimed only after the operator runs the verifier against an actual r7 result.
