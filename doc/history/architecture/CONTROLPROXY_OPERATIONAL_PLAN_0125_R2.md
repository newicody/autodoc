# 0125-r2 operational plan

0125-r2 locks the deliberation path around Scheduler orchestration and /dev/shm route exchange.

Next implementation steps:

1. Keep `DeliberationCycleCommand` as a command contract only.
2. Add a thin handler later that consumes this command through the Dispatcher.
3. Let the handler write `SpecialistDemandFrame` payloads to route refs under `/dev/shm/autodoc/routes`.
4. Specialists read demand frames and write opinion frames.
5. EventBus records observation facts and statistics only.
6. SQLContextStore persists durable cycle state.
7. GitHub remains artifact exchange only.

No daemon, watcher, GitHub client, Qdrant client, OpenVINO runtime, PostgreSQL driver, or LLM SDK is added in this patch.
