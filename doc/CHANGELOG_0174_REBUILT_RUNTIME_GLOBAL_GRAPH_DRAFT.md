# Changelog — 0174 Rebuilt runtime global graph draft

## Added

- Current-state global graph draft derived from working architecture direction.
- Maintained subgraph drafts for runtime bus, scheduler route, GitHub artifact
  dataset, vector/SQL/Qdrant, ControlProxy/RouteProxy, activity graph VisPy,
  and docs provenance.
- Rule that this patch must not rewrite `00_global.dot`.

## Not changed

- No runtime code.
- No Scheduler code.
- No VisPy renderer.
- No `00_global.dot` rewrite.
- No network, GitHub API, conversion, inference, SQL, or Qdrant execution.
