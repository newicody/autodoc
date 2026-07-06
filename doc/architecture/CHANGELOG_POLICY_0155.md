# Changelog policy — 0155

From phase 0155 onward, every significant development step must produce a changelog.

A changelog is required when a patch changes any of these surfaces:

- `src/`
- `tools/`
- `tests/`
- `doc/architecture/`
- `doc/docs/architecture/**/*.dot`
- `doc/code-rules/`
- `doc/manifests/`
- runtime contracts, route frames, SQL context records, Qdrant projections, OpenVINO/E5 handoff, Scheduler/RouteProxy boundaries

The changelog must explain:

1. what changed,
2. which existing surfaces were reused,
3. which boundaries remain unchanged,
4. which tests or smoke commands validate the step,
5. whether the phase is historical, current, partial, or planned.

The canonical graph remains:

`doc/docs/architecture/00_global.dot`

Historical phase graphs must not be deleted just because they are old. They should be marked as historical, superseded, current, partial, or planned.
