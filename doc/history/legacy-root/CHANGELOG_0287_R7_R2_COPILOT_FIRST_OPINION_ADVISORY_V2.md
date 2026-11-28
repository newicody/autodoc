# Changelog — 0287-r7-r2

## Changed

- introduced top-level `missipy.github.copilot_advisory.v2`;
- limited v2 analytical content to objective, expected result, supplied
  constraints and observable success criteria;
- added strict exact-field validation and normalization;
- changed the active producer from the v1 parser to the v2 parser;
- retained historical v1 extraction without emitting v1 from new runs;
- added deterministic executable producer tests and fail-closed tests;
- removed Chalouf from the active roadmap;
- replaced the final roadmap with generic end-to-end operational closure;
- aligned the cumulative Projects installation guide to `0287-r7-r2`.

## Unchanged

- Copilot remains optional, tool-denied and non-authoritative;
- explicit operator approval and publication gates;
- Scheduler, SQL, Qdrant, OpenVINO and laboratory boundaries;
- artifact filename and correlation metadata;
- safe Projects synchronization rules.
