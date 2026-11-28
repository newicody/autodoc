# 0175 graph heritage and operational baseline rule

0175 prevents premature graph merging.

Rules:

- Do not merge or replace `doc/docs/architecture/00_global.dot` in this phase.
- Keep old DOT graphs as heritage, orientation, historical memory, and
  inspiration.
- Mark stale graph areas as `stale-doc` instead of deleting them silently.
- Treat 0174 rebuilt graph draft and subgraphs as the immediate operational
  baseline.
- Immediate patches must follow working code surfaces and the validated
  0162..0174 chain.
- Old graphs can inspire future work, but they must not override the operational
  baseline.
- Keep GitHub as workflow/exchange/validation surface.
- Keep EventBus as observation-only.
- Keep VisPy/browser as read/projection surface.
- Keep DOT as representation, not runtime authority.
- Do not create a parallel bus, direct VisPy writer, or Scheduler bypass.

Additional exact lock:

- Keep old DOT graphs as heritage, orientation, historical memory, and inspiration.

Additional exact locks:

- 0174 rebuilt graph draft and subgraphs as the immediate operational baseline.
- Old graphs can inspire future work.
- must not override the operational baseline.
