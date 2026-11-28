# Phase 5.17 — Local server boundary

## Intent

Phase 5.17 defines the future local server boundary without implementing a server.

The local server is a future loopback control surface for the context system. It must expose explicit local operations, not hidden automation.

```text
SourceCandidateStore / ContextEngine / E5 local intake
-> local server boundary contract
-> future loopback API
-> human-controlled workflow
```

## Repository

The default projected repository remains:

```text
newicody/autodoc
```

This is metadata only. Phase 5.17 does not call GitHub.

## Contract-only state

The new module is:

```text
src/context/local_server_boundary.py
```

It defines:

```text
LocalServerEndpoint
LocalServerBoundaryPolicy
LocalServerBoundary
default_local_server_endpoints()
build_local_server_boundary()
```

The contract is serializable as:

```text
missipy.local_server.boundary.v1
```

## Planned endpoints

The planned loopback endpoints are:

```text
GET  /status
POST /source-candidates
POST /source-candidates/{candidate_id}/decision
POST /context/e5/intake
GET  /reports/{report_id}
```

They are described, not implemented.

## Boundary rules

Phase 5.17 preserves these rules:

```text
bind host documented as 127.0.0.1 only
no socket is opened
no HTTP framework is imported
no daemon is started
no polling is introduced
no network is used
no GitHub API is called
no token exists
no Qdrant is used
no LLM is called
no OpenVINO call is hidden behind the server contract
no Scheduler autoload is allowed
```

## Why not Flask or FastAPI yet?

No dependency is added in this phase. The stdlib is sufficient because we are not serving HTTP yet. We are only freezing endpoint names, payload schemas and boundary policy.

A later implementation can choose a server technology only after the boundary is stable and after the dependency is explicitly justified.

## Relationship to previous phases

```text
5.14 SourceCandidate contract
5.15 SourceCandidate local storage/report
5.16 GitHub projection design
5.17 Local server boundary
```

The local server boundary sits above local contracts and below any future external synchronization.

## Relationship to GitHub

GitHub remains a future projection surface.

The local server must not become a GitHub client by accident. Any future GitHub sync must remain a separate explicit boundary.

## Relationship to Scheduler

The local server boundary must not start the Scheduler or create a hidden daemon.

Future requests may call explicit functions, but the server must not become an implicit runtime loop unless a later phase defines that deliberately.

## Dependency statement

No non-stdlib dependency is added.
