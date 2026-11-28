# Phase 7.7 — Markdown Doc Layout Migration

Phase 7.7 adds the controlled migration step for Markdown documentation.

It complements Phase 7.6 tooling by adding a migration command that:

```text
moves Markdown files according to the documented layout
rewrites Python tests that reference moved Markdown paths
writes a migration report
```

The migration is local-only and keeps referenced documentation exploitable.
