# 0147 operational plan — dynamic artifact route refs

0147 keeps the same operator execution chain but changes the identity model:

```text
artifact_intake_contract
-> artifact_route_refs
-> existing Scheduler vector smoke
-> existing RouteProxyRuntime request/result frames
-> existing OpenVINO/Qdrant strict vector chain
```

The RouteProxy frame path now becomes artifact/job-specific instead of smoke-phase-specific. Scheduler remains the orchestrator and RouteProxy remains frame IO/data-plane.
