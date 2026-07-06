# Changelog — 0156 surface status inventory

0156 introduces a conservative status inventory before further P1/P2/P3 work.

The purpose is not to rewrite runtime code. The purpose is to classify existing
surfaces so the project does not recreate parallel runtimes, handlers, adapters,
workers, runners, orchestrators, stores, or vector backends while useful code
already exists.

## Changed

- Added a 0156 surface status inventory document.
- Added a 0156 code-rule addendum for surface reuse and deprecation discipline.
- Added a 0156 runtime architecture DOT describing the inventory pass.
- Kept `00_global.dot` untouched in this safe patch because the local graph has
  drifted and a context hunk would be brittle. The next graph refresh should be
  generated against the exact local `00_global.dot` content.

## Boundary

0156 is documentation and repository hygiene only.

It does not:

- create a Scheduler runner;
- create a SQL worker;
- create a Qdrant authority;
- create an OpenVINO reasoning runtime;
- create a RouteProxy business authority;
- create a GitHub API integration;
- delete or deprecate Python runtime code.

## Current validated P1 axis

The active P1 chain remains:

```text
artifact local
-> artifact_intake_contract
-> artifact_route_refs
-> Scheduler-shaped command
-> scheduler_route_handler_minimal.py
-> route_proxy_runtime_minimal.py
-> RouteProxy request/result frame
-> OpenVINO/E5 full vector
-> Qdrant projection/search
-> SQL persistence handoff
-> DbApiSqlContextStore.upsert_record()
-> SQL readback
```

## Status vocabulary

0156 standardizes these labels:

- `current`
- `validated`
- `partial`
- `planned`
- `historical`
- `superseded`
- `deprecated`
- `blocked`

`abandoned` is intentionally not used in 0156. A surface must first be proven
unused, duplicative, rule-violating, and safely replaced before it can move
beyond `deprecated` or `superseded`.

## Next

0157 should audit the P1 single-runner path and decide which existing operator
runner or smoke tool is extended. It must not create a parallel orchestrator.
