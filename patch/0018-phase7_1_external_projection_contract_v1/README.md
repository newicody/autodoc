# 0018 — Phase 7.1 External Projection Contract v1

This patch adds a target-neutral external projection contract.

The contract is built from the local handoff dry-run bundle and remains generic.
It does not build a GitHub payload and it does not contact any external service.

## Apply

```bash
python apply_patch_queue.py --patch 0018-phase7_1_external_projection_contract_v1 --dry-run
python apply_patch_queue.py --patch 0018-phase7_1_external_projection_contract_v1 --commit --push
```

## Scope

- Add target-neutral external projection contract module.
- Add gate-aware projection permission.
- Add item safety flags.
- Add tests, rules, docs and DOT.

## Out of scope

- No GitHub adapter.
- No external API.
- No network.
- No remote mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
