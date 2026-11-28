# Changelog — 0172 Runtime activity graph / VisPy contract

## Added

- DOT/VisPy activity graph contract.
- View mode vocabulary for architecture/runtime/artifact/scheduler/bus/score/population/debug.
- Visualization state vocabulary for lifecycle, success, failure, retry, stale,
  and superseded nodes.
- Rule that DOT is representation only and must not become command authority.
- Rule that the main `00_global.dot` graph must be patched only from exact local
  state after audit.

## Not changed

- No runtime code.
- No Scheduler modification.
- No VisPy renderer.
- No GitHub fetch.
- No conversion or inference.
