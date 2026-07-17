# Phase 0287-r7-r15-r2-r4 report

## Goal

Compose the existing Copilot v2 Issue and ProjectV2 publication surfaces into one readable, preview-first operation.

## Result

The operator now receives one combined plan. The Issue preview contains the human artifact title, Actions name, full v2 analysis and run URL. The ProjectV2 `Artefact` value contains the readable title, run URL and typed reference. One combined digest binds both surfaces.

## Safety

No mutation occurs during preview. Execute requires the global remote gate, the Issue publication gate, the ProjectV2 projection gate, operator approval and the exact combined digest. Existing adapters retain their own readbacks. Issue replay and ProjectV2 replay are no-ops.

## Reuse audit

The patch reuses the existing Copilot v2 renderer/planner, Issue adapter, ProjectV2 planner/executor and readback verifier. It adds no Scheduler, manager, worker, backend or authority.

## Next

`0287-r7-r15-r3-r1 — installed runtime factory composition` connects the server runtime before readable specialist and final-result publication.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: controlled-publication-composition
external_dependencies_added: false
scheduler_modified: false
network_boundary_added: false
existing_network_adapters_reused: true
request_remains_authoritative: true
copilot_remains_advisory: true
preview_required: true
readback_required: true
```
