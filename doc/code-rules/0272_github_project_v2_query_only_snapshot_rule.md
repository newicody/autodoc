# Rule 0272-r3 — GitHub ProjectV2 query-only snapshot

The canonical Project source is `newicody / ProjectV2 2`.  Reading it is allowed
only through a dedicated one-shot GraphQL query boundary.  GraphQL `mutation`,
issue REST enumeration, `workflow_dispatch` and all remote mutation are
forbidden.

The implementation must reuse `github_project_push_frame_config` before adding
new configuration logic.  Token values come from `token_env`, never from the
configuration file and never from serialized output.

Snapshots are local, deterministic and immutable.  SQL, Qdrant, OpenVINO,
Scheduler, EventBus, PassiveSupervisor, SHM, RouteProxy and ControlProxy are
outside this raw Project read boundary.
