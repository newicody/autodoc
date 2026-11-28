# Projects views and Actions readiness repair — 0287-r7-r15-r2-r2

## Read-only composition

```text
projectv2_views.json ───────────────┐
current ProjectV2 GraphQL readback ─┼→ pure comparison contract
workflow YAML source ───────────────┤        │
Actions permissions GET ────────────┤        ▼
selected-actions GET ───────────────┤ readiness report
workflow state GET ─────────────────┤
Copilot variable GET ───────────────┘
```

## Status model

- `projectv2_exact`: all declared fields and views match exactly;
- `authoritative_ready`: Actions and the request/artifact workflow can run;
- `copilot_ready`: the optional Copilot branch is enabled and permitted;
- `full_ready`: all three conditions are true.

The command returns success for an operational authoritative path even when
Copilot is intentionally disabled. The JSON still makes that optional-path
state explicit.

## View comparison

View identity by name is only the first check. Compliance also requires exact
layout, filter, visible-field order, board columns and vertical grouping.

## Authority boundaries

- declarative desired state: copied Projects bundle configuration;
- remote current state: GitHub GraphQL/REST readback;
- comparison: pure standard-library contract;
- mutation: absent from the new CLI;
- existing controlled reconciler: unchanged and separately digest-gated.
