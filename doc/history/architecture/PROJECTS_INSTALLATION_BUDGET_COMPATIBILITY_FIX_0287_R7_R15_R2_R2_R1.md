# Projects installation budget compatibility fix — 0287-r7-r15-r2-r2-r1

## Boundary

The readiness implementation from r15-r2-r2 is preserved. Only its cumulative
installation surface and the matching rule interpretation are corrected.

```text
safe installation commands
        |
        v
INSTALLATION.md (< 380 lines)
        |
        +--> executable preview digest uses "$PLAN_DIGEST"
        |
        +--> legacy placeholders isolated under "ne pas exécuter"
        |
        +--> Copilot false marker precedes true marker
        v
existing cumulative rules + r15-r2-r2 rules
```

Detailed operations remain in the phase reports and Copilot runbooks rather than
expanding the cumulative guide beyond its locked budget.
