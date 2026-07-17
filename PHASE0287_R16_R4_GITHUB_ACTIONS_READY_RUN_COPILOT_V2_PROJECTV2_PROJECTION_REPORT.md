# Phase 0287 r16-r4 test report

## Scope

Compose one correlated local `ready_run` with the already implemented Copilot
advisory v2 preview and ProjectV2 projection adapters.

## Acceptance

- exact run selection;
- exact three-role input;
- durable raw paths derived from repository/run/artifact IDs;
- no staging fallback and no second GitHub artifact download;
- authoritative request supplies the Issue number;
- existing v2 digest/correlation validation reused;
- existing ProjectV2 mutation gates and readback reused;
- route and confidence remain unmodified.

## Local validation performed while building the patch

```text
python -m compileall: passed
pytest focused: passed
```

Full repository `tests/rules` remains the apply-time gate.
