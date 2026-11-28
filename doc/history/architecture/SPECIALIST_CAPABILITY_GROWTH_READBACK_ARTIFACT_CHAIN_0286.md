# 0286-r7-r1 — readback artifact chain

## Corrected local flow

```text
local fixture builder
→ r5 plan JSON
→ replayed r6 result JSON
→ Issue-comment snapshot
→ ProjectV2-field snapshot
→ r7 query-only verifier
→ snapshot_ready=true
→ deployment_ready=false
```

## Real flow

```text
real r5 plan
→ r6 approved execution with --output
→ live r7 --execute query-only readback
→ deployment_ready=true only after exact correlation
```

The fixture builder never calls GitHub and marks every artifact
`fixture_only=true`. Its files must not be passed to the r6 CLI with
`--execute`.
