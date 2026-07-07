# 0188 isolated Scheduler route handler readback smoke rule

0188 proves isolated RouteProxy readback without handler execution.

Rules:

- Read isolated_scheduler_route_handler_smoke.jsonl from 0187.
- Call read_route_frame only for written_route_refs from 0187.
- Prepare RouteProxyRuntime only inside the recorded isolated runtime root.
- Do not call handle_scheduler_route_command.
- Do not call handle_scheduler_route_request.
- Do not request writer permits.
- Do not call write_route_frame.
- Verify readback does not create new frame files.
- Write only isolated_scheduler_route_handler_readback_smoke.jsonl as report output.
- Do not modify Scheduler.run.
- Do not instantiate Scheduler.
- Do not instantiate EventBus.
- Do not create a parallel bus.
- Do not write ControlProxy frames.
- Do not call GitHub API.
- Do not use network.
- Do not execute conversion.
- Do not execute inference.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
