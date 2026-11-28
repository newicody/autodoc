# Rule 0272-r2 — GitHub Actions artifact scan-once live binding

The GitHub Actions artifact scan consumes GitHub Actions artifacts only.  It
must not itself add a direct issue scan or a Project GraphQL request.  The
separate 0272-r3 ProjectV2 query-only snapshot is allowed as the canonical
Project source; the Actions artifact path remains a secondary exchange surface.

The artifact scan must reuse
`tools/run_github_actions_artifact_fetch_once.py`, remain one-shot and bounded,
and require an explicit decision for live network reads.  Only GET/download
operations are allowed inside that artifact boundary.  `workflow_dispatch` and
all remote mutation remain disabled; remote mutation is never implied by a read
scan.

Token values must come from `token_env` and must never be serialized.  Successful
artifacts are synchronized into the configured append-only local dataset through
the existing server sync surface.  SQL, Qdrant, Scheduler, SHM, RouteProxy and
ControlProxy are outside this scan boundary.
