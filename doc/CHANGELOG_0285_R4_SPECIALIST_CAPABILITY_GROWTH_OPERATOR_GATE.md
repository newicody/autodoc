# Changelog — 0285-r4 specialist capability growth operator gate

## Added

- immutable `SpecialistCapabilityGrowthDecision`;
- immutable `SpecialistCapabilityGrowthOperatorGate`;
- explicit approve, reject and defer outcomes;
- policy checks for evidence, operator allow-list, separation of duties, deprecation and
  restoration;
- deterministic policy and decision digests;
- context tests, architecture rules, report, documentation, DOT graph and manifest.

## Unchanged boundaries

- no Scheduler modification or dispatch;
- no SQL or Qdrant write;
- no EventBus publication;
- no laboratory execution;
- no GitHub or ProjectV2 mutation;
- no change to the cumulative Projects installation guide.

## Next

`0285-r5-specialist-capability-growth-durable-history`
