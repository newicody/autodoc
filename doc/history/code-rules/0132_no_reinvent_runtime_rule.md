# 0132 code_rule supplement — no reinvent runtime rule

Supplement to doc/code-rules/code_rule.md.

## Rule

No runtime wheel may be added before an existing-runtime audit.

Decision must be one of: reuse existing, extend existing, modify existing, or create new with documented gap.

## Forbidden by default

Creating a parallel Scheduler, handler, RouteProxy, OpenVINO adapter, Qdrant adapter, SQL store, or EventBus path is forbidden.

## Required preflight

Before adding or modifying a runtime/integration patch, run or document an equivalent inventory:

```bash
python tools/audit_existing_runtime_integration.py . --format markdown
```

The patch documentation must say which existing files were found and why the chosen decision is correct.

## Allowed outcomes

```text
reuse existing
extend existing
modify existing
create new with documented gap
```

`create new with documented gap` is only allowed when no existing surface fits after the audit.

## Scheduler boundary

`Scheduler.run()` must not be modified as part of opportunistic integration.  It can only be changed by a dedicated Scheduler migration patch with explicit rule updates and tests.
