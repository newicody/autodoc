# Phase 0287-r7-r4 — Copilot advisory v2 operator/laboratory projection

## Objective

Extend the existing 0281 operator/laboratory projection so validated historical
v1 advisories and first-opinion v2 advisories both reach the existing laboratory
path without sharing or silently reinterpreting analytical fields.

## Reuse audit

Reused and extended:

- `src/context/github_operator_laboratory_advisory_projection_0281.py`;
- the existing 0275 read-only intake;
- the existing operator decision and policy gate;
- the existing fake-laboratory command and platform Scheduler;
- the existing context-reference injection and authority directives.

Not added:

- no new runner, adapter, prompt manager, laboratory manager or orchestrator;
- no Scheduler modification or creation;
- no SQL, Qdrant, OpenVINO or EventBus write;
- no GitHub or ProjectV2 mutation;
- no external dependency.

## Versioned projection decision

The historical projection remains
`missipy.github.copilot_advisory_laboratory_context.v1` and keeps its v1 fields.
The first-opinion projection uses
`missipy.github.copilot_advisory_laboratory_context.v2` and exposes only:

- `concrete_objective`;
- `expected_result`;
- `provided_constraints`;
- `success_criteria`.

The builder dispatches on the validated source advisory schema. It never maps a
v1 summary or route into a v2 objective or result.

## Publication preview boundary

The v1 preview remains unchanged. The v2 projection produces
`missipy.github.copilot_advisory_publication_preview.v2` with the same four
first-opinion fields and the existing technical references and safety gates.
No Markdown publication plan or remote mutation is added in this phase.

## Authority and orchestration

The authoritative request remains the source of candidate content. Copilot is
hint-only. The projection adds one context reference and version metadata to the
already supplied laboratory command. The existing Scheduler remains the only
orchestration authority.

code_rule_review: done
code_rule_update_required: false
code_rule_reason: changed public projection meaning is carried by explicit v2
schemas while v1 remains unchanged.

live_path_status: transition

Validation covers v1 preservation, v2 strict projection, v2 preview shape,
invalid array rejection, existing laboratory delegation, idempotent context
generation and locked no-mutation/no-new-Scheduler flags.

This phase closes operator/laboratory projection only. Controlled publication
rendering and planning for preview v2 remain the next patch.
