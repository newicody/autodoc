# 0284-r1-r3-r4 — GitHub project connector trigger contract fix

Apply this patch on the dirty worktree left by the failed
`0284-r1-r3-r2-github-project-connector-rule-migration` full-suite run.

It does not touch the existing Graphviz document and does not reapply r3-r1 or
r3-r2. It repairs only the read-only artifact trigger contract, the readiness
example, the compatibility rule and the cumulative Projects installation guide.

Suggested commit:

```text
split-github-project-connector-configs
```
