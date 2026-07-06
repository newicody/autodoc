# code_rule supplement for Scheduler route handler membrane

This supplement applies from 0131 onward.

## Rule

A Scheduler route handler is an executor bridge, not an orchestrator.

Allowed:

- consume immutable command/frame request data;
- ask RouteProxyRuntime for a writer permit;
- write/read route frames through runtime helpers;
- return observation-ready facts to the caller;
- stay importable and testable without daemon/service setup.

Forbidden:

- instantiate or mutate Scheduler;
- modify `Scheduler.run()`;
- bypass Dispatcher/Policy/Queue boundaries in live integration;
- import OpenVINO, Qdrant, PostgreSQL clients, GitHub clients, network clients, VisPy, or EventBus runtime;
- publish heavy payloads to EventBus;
- make business decisions about specialists or final synthesis.

code_rule supplement for Scheduler route handler membrane.
