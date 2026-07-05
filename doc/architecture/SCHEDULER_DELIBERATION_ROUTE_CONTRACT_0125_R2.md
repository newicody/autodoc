# 0125-r2 — Scheduler deliberation route contract

Scheduler is the deliberation orchestrator. No parallel local server orchestrator is introduced.

0125-r2 replaces the rejected local-orchestrator direction with a contract that can be scheduled through the existing kernel path later:

```text
DeliberationCycleCommand
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
-> /dev/shm route frames
-> specialist workers
-> EventBus observation facts
-> SQL durable state
```

Do not modify Scheduler.run() in 0125-r2. The patch only defines immutable contracts and deterministic builders.

## Boundaries

GitHub exchanges artifacts only: artifact in and final artifact out. Internal specialist navettes, search statistics, route frames, and VisPy supervision material do not belong in GitHub.

/dev/shm route frames are a multitask data-plane interface for local workers and a future grid. They are useful now for fast local multitask exchange and later for extending the architecture across a grid. /dev/shm is not durable authority.

EventBus observes facts, statistics, and paths, not payload commands. The bus can record `scheduler.dispatched_round`, `route.frame_written`, `specialist.explored_axis`, and `server.refined_demand`; the heavy frames stay on route refs.

SQLContextStore is durable context authority. Durable decisions, accepted context changes, and final synthesis state must be persisted there.

Qdrant is vector projection and retrieval, not context authority. It returns refs that must be rehydrated from SQL.

E5/OpenVINO is embedding only behind adapter, not decision maker. E5 produces vectors from `query:` and `passage:` text, but does not validate, synthesize, or orchestrate.

Specialist proposals are receivable as analysis signals before final validation. A proposal can trigger another specialist, another model, a context patch proposal, or a rejection explanation without being accepted as the final answer.

## Route frame examples

```text
route:deliberation/cycle-42/round-0001/demand-thermal
route:deliberation/cycle-42/round-0001/opinion-thermal
```

Concrete payloads live under:

```text
/dev/shm/autodoc/routes/deliberation/cycle-42/round-0001/demand-thermal.frame
/dev/shm/autodoc/routes/deliberation/cycle-42/round-0001/opinion-thermal.frame
```

The Scheduler carries refs and commands. The specialists read and write route frames. EventBus only observes. SQL persists.
