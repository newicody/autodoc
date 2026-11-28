# Rule 0272-r5 — GitHub Project system deployment readiness

1. The readiness surface tests an existing installation and deployment only.
2. It must not install, copy, commit, push or deploy any file.
3. It must not dispatch, enable, disable or mutate a GitHub Actions workflow.
4. GitHub access is limited to ProjectV2 GraphQL query operations and REST GET.
5. Token values come from `token_env` and are never serialized.
6. The deployed workflow must have no `workflow_dispatch`, write permission or mutation command.
7. Local and remote workflow/builder contents are compared by digest.
8. SQL, Qdrant, Scheduler, EventBus, SHM, RouteProxy and ControlProxy remain untouched.
9. ProjectV2 remains the canonical GitHub read source; Actions artifacts remain secondary.
