# Changelog — 0199 Controlled dev RouteProxy smoke execution

## Added

- Controlled dev RouteProxy smoke execution wrapper.
- Explicit reuse of `tools/run_isolated_route_pipeline_smoke.py`.
- Controlled dev execution report.
- `execution_unlocked_by_p0199=true`.
- `execution_allowed_by_0199=true`.
- P0200 post-execution audit requirement.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No new runtime handler.
- No new adapter.
- No new bus.
- No new SQL backend.
- No new Qdrant backend.
- No new GitHub client.
- No new graph renderer.
- No new inference path.
- No Scheduler.run modification.
- No ControlProxy frame write.
- No production route write.
