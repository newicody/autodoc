# Changelog 0238 — passive supervisor visual pipeline smoke

## r1

Added a local read-only pipeline command that composes:

```text
0234 -> 0236 -> 0237
```

The command generates the all-surfaces smoke report, visual read-model, and
visual layout model in order under `.var/reports`.
