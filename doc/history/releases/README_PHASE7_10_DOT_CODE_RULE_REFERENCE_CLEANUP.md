# Phase 7.10 — DOT code_rule Reference Cleanup

Phase 7.10 adds the controlled cleanup step for architecture DOT graphs.

The cleanup removes lines that mention:

```text
code_rule
code-rule
code rule
```

from `.dot` files under `doc/docs/architecture`.

This keeps diagrams focused on architecture instead of documentation-rule audit
plumbing.
