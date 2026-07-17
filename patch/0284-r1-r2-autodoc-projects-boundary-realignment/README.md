# 0284-r1-r2 — Autodoc / Projects boundary realignment

This patch removes Project-management surfaces that are active in the Autodoc
repository while preserving the reusable `projects-repository` copy bundle and
all explicit GitHub connector adapters.

It intentionally does not split the mixed query-only / workflow-dispatch
configuration. That migration requires changing the existing outbound adapter
and belongs to the next unitary patch.

Suggested commit:

```text
realign-autodoc-projects-repository-boundary
```
