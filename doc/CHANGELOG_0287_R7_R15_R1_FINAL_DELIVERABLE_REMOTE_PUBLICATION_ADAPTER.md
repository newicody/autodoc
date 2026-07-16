# Changelog — 0287-r7-r15-r1

## Added

- transport-neutral controlled execution of the immutable r13 final publication
  plan;
- parser for direct r13 plan mappings and nested r14 result mappings;
- Issue and ProjectV2 publication protocols;
- preview, create/update, replay, collision and partial-execution semantics;
- exact post-mutation readback through the existing r13 verifier;
- GitHub CLI REST/GraphQL adapter with three environment locks and exact digest
  confirmation;
- functional, tool and rule tests;
- architecture, report and manifest documentation.

## Unchanged

- Scheduler and dispatch;
- laboratory and specialist execution;
- SQL durable authority;
- Qdrant recall/projection;
- OpenVINO/E5 embedding;
- r13 publication body, projection and digest calculation;
- GitHub workflow templates and installation.

## Roadmap

This is the first unit of r15. It does not claim real GitHub closed-loop
evidence. `r15-r2` will correlate one imported Actions run with r14 and this
adapter; `r15-r3` will record the actual Issue plus ProjectV2 evidence and
idempotent replay.
