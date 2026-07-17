# 0284-r1-r2-r1-v3 — Autodoc / Projects boundary documentation compatibility

Apply this patch on the dirty worktree left after
`0284-r1-r2-autodoc-projects-boundary-realignment` applied successfully but
failed its historical 0272 rule gate.

This version replaces both earlier `r2-r1` corrective bundles. It does not
modify the historical test file. It restores the exact legacy documentation
markers while keeping them explicitly scoped as compatibility terminology.

Suggested commit:

`realign-autodoc-projects-repository-boundary`
