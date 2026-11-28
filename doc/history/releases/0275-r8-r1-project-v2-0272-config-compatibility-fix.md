# 0275-r8-r1 — ProjectV2 0272 config compatibility fix

This microfix restores every established 0272 value that was changed by
0275-r8 while retaining the isolated `[workflow_dispatch]` section used for
`newicody/projects`.

The query-only snapshot, readiness fixture and optional legacy bridge remain
backward compatible. The new `En cours` dispatcher remains available through
its own config section and bounded runner.
