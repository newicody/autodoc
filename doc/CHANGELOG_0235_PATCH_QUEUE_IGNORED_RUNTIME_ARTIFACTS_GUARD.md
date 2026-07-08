# Changelog 0235 — patch queue ignored runtime artifacts guard

## r3

Patch queue commit selection now excludes `.var/` runtime artifacts before
calling `git add`.

This prevents local reports such as:

```text
.var/reports/eventbus_supervision_reuse_findings_triage_0229.json
```

from breaking automatic commits when `.var/` is ignored by `.gitignore`.

The patch preserves the existing `patch/` artifact policy:

- `patch/` is excluded by default.
- `patch/` is included only with `--include-patch-artifact`.
