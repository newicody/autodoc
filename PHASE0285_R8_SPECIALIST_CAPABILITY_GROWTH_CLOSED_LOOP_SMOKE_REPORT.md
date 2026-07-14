# Phase 0285-r8 — specialist capability growth closed-loop smoke

## Status

Implemented as one additive composition layer over the existing 0285-r2 through
0285-r7 contracts and the existing 0284-r5 portable-specialist laboratory smoke.

## Proven path

`evidence → proposal → operator approval → immutable revision → SQL-authoritative history → Scheduler-approved selection → existing laboratory execution → EventBus observation → passive read model`

The smoke also constructs explicit `reject` and `defer` decisions and proves that
both are rejected by the r5 history command before any history-port call. Therefore
neither outcome can reach Scheduler selection or laboratory execution.

## Reuse boundary

- `PortableSpecialistDescriptor` and revision lineage are reused.
- The r4 operator gate remains the only revision authorization gate.
- The r5 SQL history port remains the durable authority.
- The r6 Scheduler selection event and handler are reused.
- The 0284-r5 portable-specialist existing-chain smoke remains the laboratory path.
- The r7 EventBus projection and passive read model remain observation-only.

No Scheduler, Dispatcher, EventBus, queue, registry, laboratory provider or durable
store is created by the r8 module.

## Safety boundaries

- Qdrant is not an authority and receives no r8 write.
- GitHub and ProjectV2 are not mutated.
- The deterministic fake laboratory is still the executed backend for this smoke.
- A real specialist backend is not claimed.
- Cross-laboratory transfer is not executed.

## `newicody/projects` installation review

`templates/github/projects-repository/INSTALLATION.md` was reviewed. No update is needed because r8 adds no workflow, issue form, ProjectV2 field, variable, secret,
permission or deployment action. Copilot remains disabled by default and repository
synchronization remains without `--delete`.

## Next boundary

The generic 0285 capability-growth chain is closed. The next work must start with a
reuse audit before exposing the operator decision/status workflow through
`newicody/projects`; the GitHub surface must remain non-authoritative.
