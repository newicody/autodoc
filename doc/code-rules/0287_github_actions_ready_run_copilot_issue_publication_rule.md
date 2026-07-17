# Code rule 0287 — ready-run Copilot Issue publication

1. The `newicody/projects` workflow MUST remain `issues: read` and MUST NOT
   publish or update Issue comments itself.
2. Automatic comment publication MUST start from a valid local
   `missipy.github_actions.artifact_scan_once_live.v1` result and a strict
   three-role `ready_run`.
3. The publisher MUST read artifact members from the durable `raw` server
   dataset.  A staging path MUST NOT be the durable execution authority.
4. The existing Copilot v2 preview builder and existing controlled Issue
   publication adapter MUST be reused.
5. Execute mode MUST require a policy decision, operator approval, the remote
   mutation gate, and the Issue publication gate.
6. The exact plan digest produced by preview MUST be passed to execute.
7. A local completion receipt MUST be written only after verified GitHub
   readback.  Idempotent replay MAY produce a completion receipt.
8. Loss of local state MUST remain recoverable through the existing marked
   comment replay behavior.
9. This unit MUST NOT download Actions artifacts, mutate ProjectV2 fields,
   write SQL/Qdrant, change Scheduler, or start a laboratory.
10. The authoritative request and advisory classification MUST remain distinct.
