# Phase 0269 test report - Production prototype smoke composition

## Source baseline

```text
758312df52ad04c9fee6651978dd54274e9d528a
r2-openrc-launcher-minimal-readiness-artifact-closure
```

## Existing surface audit

The existing `run_p1_closed_loop_operator_smoke.py` targets 0145/0148/0151.
0269 reuses the nine current phase tools directly and adds no runtime manager.

## Construction validation

```text
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_production_prototype_smoke_composition_0269.py \
  tests/tools/test_run_production_prototype_smoke_composition_0269.py \
  tests/rules/test_production_prototype_smoke_composition_0269_rule.py
```

Focused construction result: `10 passed`.

The complete repository suites remain patch-queue gates on the target checkout.

## Plan smoke

```text
PYTHONPATH=src:. python tools/run_production_prototype_smoke_composition_0269.py \
  --output .var/reports/production_prototype_smoke_composition_0269.json \
  --format summary
```

## Execute smoke

Real OpenVINO/E5 with the currently explicit demo Qdrant membrane:

```text
PYTHONPATH=src:. python tools/run_production_prototype_smoke_composition_0269.py \
  --execute \
  --policy-decision-id policy:0269:operator \
  --demo-eventbus \
  --demo-qdrant \
  --output .var/reports/production_prototype_smoke_composition_0269.json \
  --format summary
```

For a deterministic test-only embedding, add `--demo-embedding` explicitly.
Omit `--demo-eventbus` to build the 0265 facts without publishing them through
the in-memory demonstration bus.

## Boundary

The CLI launches only the existing Python phase tools. It does not start an
external service, call OpenRC, mutate GitHub, or modify Scheduler.run.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing typed CLI/use-case/result and IO-boundary rules cover 0269
live_path_status: transition
live_path_uses_real_backend: true when OpenVINO is used; Qdrant remains explicit demo
context_contract_version: autodoc.production_prototype_smoke_composition.v1
context_contract_changed: false
search_commands_bounded: n/a
non_stdlib_dependencies_added: none
```
