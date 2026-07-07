# 0200 controlled dev RouteProxy smoke post-execution acceptance rule

0200 accepts Bloc B after P0199 execution.

Rules:

- Read controlled_dev_routeproxy_smoke_execution.json from 0199.
- Reuse existing pipeline artifacts from P0199.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not execute controlled-dev-routeproxy-smoke in 0200.
- Do not add a new runtime handler.
- Do not add a new adapter.
- Do not add a new bus.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new GitHub client.
- Do not add a new graph renderer.
- Do not add a new inference path.
- Require execution_success true.
- Require pipeline_success true.
- Require frames_written_count 1.
- Require readback_count 1.
- Require ControlProxy frames false.
- Require Scheduler modified false.
- Require EventBus instantiated false.
- Require network used false.
- Require policy_scoped_queued_count equals queued_count.
- Require pipeline artifacts to exist under target_runtime_root.
- Append controlled_dev_routeproxy_smoke_registry.jsonl when requested.
- Open Bloc C only after acceptance.
- Do not approve production route writes.
- Do not import runtime handler modules.
- Do not call handle_scheduler_route_command.
- Do not call handle_scheduler_route_request.
- Do not call prepare_route_proxy_runtime.
- Do not call read_route_frame.
- Do not request writer permits.
- Do not call write_route_frame.
- Do not write ControlProxy or RouteProxy frames.
- Do not modify Scheduler.run.
- Do not instantiate Scheduler.
- Do not instantiate EventBus.
- Do not create a parallel bus.
- Do not call GitHub API.
- Do not use network.
- Do not execute conversion.
- Do not execute inference.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
