# Changelog — 0275-r4 GitHub dual-artifact SourceCandidate intake

## Added

- verified dual-artifact digests and correlation;
- built SourceCandidate only from the request;
- retained advisory refs as non-authoritative provenance.

## Boundaries

- one existing Scheduler only;
- SQL remains durable authority;
- GitHub mutation remains closed unless this phase explicitly reaches the guarded adapter;
- no secret is serialized.
