# Automatic ProjectV2/runtime resolution — 0287-r7-r15-r2-r1

## Normal operator path

```text
run id + repository + candidate decision
        │
        ├── github_project_v2_query_only.ini
        │     ├── owner
        │     ├── number
        │     └── token_env
        │
        ├── love_actions_closed_loop.ini
        │     └── real runtime factory module:function
        │
        ▼
three correlated Actions artifacts
        │ authoritative request → issue_number
        ▼
read-only GraphQL resolution
        ├── exact ProjectV2
        ├── exact Issue item
        └── exact configured field
        ▼
r14 real-port composition
        ▼
r15-r1 mandatory preview
        ▼
love-r14-result-<RUN_ID>.json
```

## Authority boundaries

- authoritative request: source Issue identity;
- existing ProjectV2 configuration: owner and project number;
- read-only GraphQL: current item and field identities;
- installed runtime configuration: one explicit real factory reference;
- Scheduler/SQL/OpenVINO/Qdrant: unchanged injected authorities;
- r15-r1: preview computation;
- remote mutation: absent.

## Overrides

Low-level ProjectV2 identifiers and `--runtime-factory` remain available only
for diagnostics and controlled substitutions. If one item override is supplied,
the matching field override is required too. Both are still checked against the
read-only GraphQL response.
