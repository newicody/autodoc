# Changelog — 0274-r2 fake laboratory deliberation composition

## Added

- bounded command for a fake laboratory deliberation;
- one existing-Scheduler visit per requested specialist;
- deterministic mapping from fake results to preliminary opinions;
- refined demands only for follow-up stances;
- existing `DeliberationRound` and bus-statistics composition;
- existing liaison synthesis and final packet composition;
- local `FinalArtifactEnvelope` only after complete convergence;
- deterministic replay, architecture and rule tests.

## Not added

- no Scheduler, queue, EventBus, registry or orchestrator;
- no SQL write or Qdrant projection;
- no GitHub mutation;
- no network or external dependency.
