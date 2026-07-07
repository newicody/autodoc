# 0174 rebuilt runtime global graph draft rule

0174 creates a current-state graph draft and subgraph drafts without replacing
`doc/docs/architecture/00_global.dot`.

Rules:

- Treat 0174 graphs as representation drafts, not runtime authority.
- Do not replace `00_global.dot` in this patch.
- Deduce the graph from code surfaces, tests/rules/manifests, and the validated
  0162..0173 chain.
- Treat stale docs and changelogs as historical context, not sole truth.
- Mark stale areas with `stale-doc`.
- Keep GitHub as workflow/exchange/validation surface.
- Keep configured server dataset and SQL/local stores as authority surfaces.
- Keep Qdrant as projection/search, not durable authority.
- Keep EventBus as observation-only.
- Keep VisPy/browser as a read/projection surface.
- Do not create a parallel bus, direct VisPy writer, or Scheduler bypass.

Required graph files:

- `doc/docs/architecture/runtime/174_rebuilt_runtime_global_current_state.dot`
- `doc/docs/architecture/runtime/0174_subgraphs/runtime_bus.dot`
- `doc/docs/architecture/runtime/0174_subgraphs/scheduler_route.dot`
- `doc/docs/architecture/runtime/0174_subgraphs/github_artifact_dataset.dot`
- `doc/docs/architecture/runtime/0174_subgraphs/vector_sql_qdrant.dot`
- `doc/docs/architecture/runtime/0174_subgraphs/controlproxy_routeproxy.dot`
- `doc/docs/architecture/runtime/0174_subgraphs/activity_graph_vispy.dot`
- `doc/docs/architecture/runtime/0174_subgraphs/docs_provenance.dot`
