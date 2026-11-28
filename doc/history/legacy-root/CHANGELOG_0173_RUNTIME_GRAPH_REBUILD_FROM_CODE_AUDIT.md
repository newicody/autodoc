# Changelog — 0173 Runtime graph rebuild from code audit

## Added

- Method for rebuilding stale DOT architecture graphs from working code,
  manifests, rules, tests, and the planned 0162..0172 chain.
- Required subgraph list for global/runtime/scheduler/GitHub/vector/controlproxy/
  VisPy/docs-provenance views.
- Rule that changelog holes are documentation gaps, not proof that code surfaces
  do not exist.
- Rule that `00_global.dot` must not be patched from stale assumptions.

## Not changed

- No runtime code.
- No Scheduler code.
- No VisPy code.
- No `00_global.dot` rewrite.
- No network, GitHub API, conversion, inference, SQL, or Qdrant execution.
