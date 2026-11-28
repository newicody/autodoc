# 0187 isolated Scheduler route handler smoke rule

0187 is the first controlled isolated handler execution smoke.

Rules:

- Read isolated_handler_execution_plan.jsonl from 0186.
- Execute only ready plan items.
- Call handle_scheduler_route_command only with RouteProxyRuntimePolicy rooted in isolated_runtime_root.
- Verify written frame paths stay under isolated_runtime_root.
- Write only isolated_scheduler_route_handler_smoke.jsonl as report output.
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
