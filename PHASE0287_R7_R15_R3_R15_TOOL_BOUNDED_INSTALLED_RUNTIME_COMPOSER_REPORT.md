# Phase 0287-r7-r15-r3-r15 — Tool-bounded installed runtime composer

## Result

A concrete provider now composes one process-local runtime from the installed
PostgreSQL, multilingual-E5 OpenVINO and Qdrant services.

The provider creates exactly one canonical Scheduler stack for the tool
invocation and returns it inside the existing imported-Actions runtime lease.
The CLI remains responsible for running and stopping that Scheduler.

## Ownership

The lease owns two synchronous cleanup hooks:

1. PostgreSQL authority binding;
2. Qdrant client.

Hooks execute in reverse order, therefore Qdrant closes before PostgreSQL.
OpenVINO remains process-local through the existing pipeline bundle and exposes
no separate close hook.

## Gates

Live composition requires independent explicit environment gates for Qdrant
point writes and Qdrant searches. Secrets are read from configured environment
variable names and never placed in attestations or receipts.

## Deferred

The existing Actions CLI still invokes the historical deterministic smoke entry
point. The next unit switches that single call to the r14 live smoke function.
