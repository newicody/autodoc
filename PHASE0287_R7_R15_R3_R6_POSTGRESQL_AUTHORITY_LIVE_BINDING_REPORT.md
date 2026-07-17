# Phase 0287-r7-r15-r3-r6 — PostgreSQL authority live binding

## Decision

The installed love runtime now has one explicit PostgreSQL I/O boundary.  It
reuses `DbApiContextRevisionAuthorityStore`; there is **no new authority store**,
no repository abstraction, no RuntimeManager and no parallel orchestrator.

## Live path

1. consume validated `ManualInstalledRuntimeSettings`;
2. read the password only from the configured environment variable;
3. lazily resolve `psycopg.connect` or accept an injected DB-API connector;
4. create/select the configured PostgreSQL schema idempotently;
5. reuse the existing DB-API authority with `paramstyle="format"`;
6. initialize the existing authority tables;
7. seed `context-revision:love-base` as a deterministic empty accepted root;
8. expose `binding.close` for the later tool-bounded runtime lease.

## Boundaries

- SQL is the durable authority.
- Password values are never serialized or echoed in sanitized errors.
- The root seed is immutable and idempotent.
- No Scheduler or Dispatcher is created.
- No OpenVINO inference is performed.
- No Qdrant write or read is performed.
- E5/Qdrant remain deferred to later units.

## Next unit

`0287-r7-r15-r3-r7-openvino-e5-query-adapter-async-alignment` will decide and
implement the scheduler-safe E5 query adapter without calling `asyncio.run`
inside the active Scheduler loop.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: the existing explicit I/O adapter and external dependency rules already cover this boundary
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: true
scheduler_modified: false
network_added: true
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```

External dependency declaration:

- library: `psycopg` v3;
- reason: Python's standard library has no PostgreSQL DB-API driver;
- allowed boundary: lazy import only in
  `love_postgresql_authority_binding_0287.py`;
- containment tests: the connector is injected in unit tests and cumulative
  rules forbid Scheduler, OpenVINO and Qdrant construction in this module.
