# 0173 runtime graph rebuild from code rule

0173 locks the method for rebuilding architecture graphs.

Rules:

- Do not use stale DOT or stale changelog entries as the only source of truth.
- Prefer working code surfaces, passing tests, manifests, and code-rules over
  outdated graph documentation.
- Changelog gaps must be marked as documentation gaps, not interpreted as proof
  that a working surface does not exist.
- Rebuild the global graph from current code and the validated 0162..0172 chain.
- Preserve historical roadmap notes when they help humans/AI understand the
  development path.
- Mark stale graph/doc areas explicitly with `stale-doc`.
- Do not patch `doc/docs/architecture/00_global.dot` from assumptions.
- Any future `00_global.dot` refresh must be based on the exact local file.
- Runtime graph nodes must not become command authority.
- DOT remains representation; Scheduler/policy/zone remain authority.
- VisPy/browser must remain a reader/projection surface over existing bus facts.
- Do not create a parallel bus or direct VisPy writer for graph display.

Minimum subgraphs to maintain:

- global
- runtime-bus
- scheduler-route
- github-artifact-dataset
- vector-sql-qdrant
- controlproxy-routeproxy
- activity-graph-vispy
- docs-provenance
