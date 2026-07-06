# 0133 code_rule supplement — extend existing runtime surfaces

Before creating a new runtime, handler, worker, or adapter module, check the 0132 integration audit and the repository surfaces it lists.

For 0133:

- Do not create a new route handler or runtime wheel when audited surfaces exist.
- Do not create fake_specialist_worker_minimal.py in 0133.
- Extend `src/runtime/scheduler_route_handler_minimal.py` for this route handler step.
- Reuse `src/runtime/route_proxy_runtime_minimal.py` for frame IO.
- Scheduler remains the orchestrator.
- RouteProxyRuntime remains the IO executor.
- Scheduler.run() is not modified.
- EventBus receives observation-ready facts only.
- OpenVINO and Qdrant remain out of this handler patch.

Any future exception must document the missing capability and why reuse/extension cannot work.
