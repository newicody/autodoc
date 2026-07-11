# Rule 0272-r1 — GitHub read-only reuse audit

Before adding a GitHub issue scan backend, audit and reuse the existing read-only Actions
transport, `token_env` validation, repository allow-list, 0267 handoff and remote mutation
gate. The read path must never import or invoke the mutation-facing fake adapter.

The audit itself is offline. A future issue scan command must be one-shot and bounded,
must use GET-only operations, must keep token values out of reports, and must publish
`remote_mutation_allowed=False`.
