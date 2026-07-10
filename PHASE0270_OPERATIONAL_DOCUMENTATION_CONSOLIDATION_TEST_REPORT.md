# Phase 0270 test report — Operational documentation consolidation

## Source baseline

```text
d7fce0c392399b356f5ae789e5f094d613c1915a
r1-production-prototype-smoke-composition
```

## Existing surface audit

0270 reuses and updates the existing canonical entrypoints: root README,
`CURRENT_ARCHITECTURE_STATE_0154.md`, `ARCHITECTURE_LAYERS.md` and
`00_global.dot`. It does not create a second current-state index or master graph.

## Construction validation

```text
PYTHONPATH=src:. python -m pytest -q \
  tests/rules/test_operational_documentation_consolidation_0270_rule.py

dot -Tdot \
  doc/docs/architecture/00_global.dot \
  -o /tmp/00_global_0270.dot

dot -Tdot \
  doc/docs/architecture/runtime/270_operational_documentation_consolidation.dot \
  -o /tmp/270_operational_documentation_consolidation.dot
```

Focused construction result is recorded in the patch metadata. Complete
repository suites remain patch-queue gates on the target checkout.

## Boundary

0270 performs no runtime operation. It does not call SQL, Qdrant, OpenVINO,
GitHub or OpenRC; does not start a service; and does not modify `Scheduler.run()`.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing documentation, reuse-first and boundary rules cover 0270
live_path_status: documentation-only
live_path_uses_real_backend: false
context_contract_changed: false
non_stdlib_dependencies_added: none
```


## r2 compatibility correction

The first target patch-queue run exposed six existing-rule regressions: four root
README entrypoint assertions and two 0154 current-state compatibility assertions.
r2 preserves the 0270 consolidation while restoring those stable contracts and
removing the forbidden `Scheduler.run(` signature spelling from the 0154 page.

Focused validation includes the root README, 0154 current-state and 0270 rule
suites. The complete repository suites remain mandatory patch-queue gates.
