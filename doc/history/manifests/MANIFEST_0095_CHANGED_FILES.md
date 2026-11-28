# Manifest 0095 — locked route generation materializer

```text
src/runtime/route_generation_locked_materializer.py
tests/runtime/test_route_generation_locked_materializer.py
tests/rules/test_route_generation_locked_materializer_rule.py
doc/architecture/ROUTE_GENERATION_LOCKED_MATERIALIZER_0095.md
doc/manifests/MANIFEST_0095_CHANGED_FILES.md
PHASE0095_TEST_REPORT.md
```

0095 adds a small locked façade around the existing generation materializer. It
keeps the patch scope intentionally narrow and does not edit the existing table
or lock primitive modules.
