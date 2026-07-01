# Phase 5.17 — Local server boundary

This archive introduces a contract-only local server boundary for the future local control surface.

## Goal

```text
SourceCandidateStore / ContextEngine / E5 status
-> LocalServerBoundary
-> future loopback API contract
```

The server is not implemented in this phase.

## Main additions

```text
src/context/local_server_boundary.py
tests/context/test_local_server_boundary.py
doc/LOCAL_SERVER_BOUNDARY.md
doc/docs/architecture/context/41_local_server_boundary.dot
```

## Planned endpoints

```text
GET  /status
POST /source-candidates
POST /source-candidates/{candidate_id}/decision
POST /context/e5/intake
GET  /reports/{report_id}
```

These endpoints are descriptions only. They do not bind a socket and do not serve HTTP.

## Repository metadata

```text
newicody/autodoc
```

This remains local metadata only. No GitHub API is called.

## Boundaries

```text
no server implementation
no socket opened
no Flask/FastAPI dependency
no network
no GitHub API
no token
no daemon
no polling
no Scheduler autoload
no Qdrant
no LLM
no OpenVINO call
```

## Dependency statement

No non-stdlib dependency was added.

## Apply

```bash
tar -xzf autodoc_phase5_17_local_server_boundary.tar.gz
```

## Suggested tests

```bash
PYTHONPATH=src pytest -q tests/context/test_local_server_boundary.py
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.17 adds a pure local server boundary contract without implementing IO or adding dependencies; no programming rule update is required.
```
