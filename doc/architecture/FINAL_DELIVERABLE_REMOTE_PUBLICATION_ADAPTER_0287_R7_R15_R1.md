# Final deliverable remote publication adapter — 0287-r7-r15-r1

## Placement

The adapter sits after the pure r13 publication plan. It is not part of the
laboratory, Scheduler, memory or synthesis path.

```text
r14/r13 JSON
  │
  ▼
plan parser in src/context
  │
  ├── Issue read port ───────────────┐
  └── ProjectV2 read port ──────────┤
                                     ▼
                         preflight decision
                    create/update/replay/collision
                                     │
                     preview ────────┤
                                     │ execute
                                     ▼
                    operator + 3 locks + digest
                                     │
                         Issue create if needed
                                     │
                     ProjectV2 update if needed
                                     │
                         exact remote readback
                                     │
                         existing r13 verifier
```

## Domain versus transport

`src/context/love_final_deliverable_remote_publication_0287.py` owns only the
controlled decision and execution semantics against injected protocols.

`tools/publish_love_final_deliverable_0287.py` owns:

- environment locks;
- argument and JSON-file parsing;
- GitHub CLI subprocess execution;
- REST and GraphQL payloads;
- output formatting.

This boundary permits deterministic tests without network access and prevents
GitHub transport concerns from entering the domain layer.

## Mutation ordering

The r13 operation dependency is preserved:

1. create the final Issue comment when absent;
2. project the concise value into ProjectV2 when different;
3. reread both surfaces;
4. accept success only through the exact r13 verifier.

A ProjectV2 failure after Issue creation is intentionally visible as partial.
The marker makes the next execution idempotent on the Issue side.

## ProjectV2 field support

The adapter resolves the field by exact node id and checks the expected name.
It supports the GraphQL value forms used by ProjectV2:

- text;
- single-select by exact option name;
- date;
- number.

Unsupported field kinds fail closed before mutation.

## Closed boundaries

The adapter cannot:

- create or call a Scheduler;
- invoke a specialist or laboratory;
- write SQL;
- write or query Qdrant;
- call OpenVINO;
- rebuild a final synthesis;
- alter the approved r13 body, projection or digest.
