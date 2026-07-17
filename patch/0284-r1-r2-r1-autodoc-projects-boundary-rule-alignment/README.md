# 0284-r1-r2-r1 — Autodoc / Projects boundary rule alignment

Apply this recovery patch directly on the dirty worktree left by the failed
`0284-r1-r2-autodoc-projects-boundary-realignment` gate.

It updates the historical 0272 rule that still required the removed
`Project-native` wording. The patch queue commit step stages every dirty tracked
and untracked non-patch file, so the final commit also includes the already
applied r2 boundary changes.

Suggested commit:

```text
realign-autodoc-projects-repository-boundary
```
