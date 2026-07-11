# Rule 0272-r2 — GitHub Actions artifact scan-once live binding

The local GitHub read path consumes GitHub Actions artifacts only. A direct issue
scan or direct Project GraphQL scan must not be added while the configured Action
artifact path exists.

The scan must reuse `tools/run_github_actions_artifact_fetch_once.py`, remain
one-shot and bounded, and require an explicit decision for live network reads.
Only GET/download operations are allowed. `workflow_dispatch` and all remote
mutation remain disabled; remote mutation is never implied by a read scan.

Token values must come from `token_env` and must never be serialized. Successful
artifacts are synchronized into the configured append-only local dataset through
the existing server sync surface. SQL, Qdrant, Scheduler, SHM, RouteProxy and
ControlProxy are outside this scan boundary.
