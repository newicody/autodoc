# Phase 0274-r3 test report — fake laboratory closed local handoff

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_fake_laboratory_closed_local_handoff_0274.py
PYTHONPATH=src:. python -m pytest -q
```

## Covered behavior

- dry-run builds SQL, passive, visual and GitHub preview material without effects;
- execute persists and reads back the immutable specialist output;
- controlled E5 compatibility and Qdrant projection succeed with injected fakes;
- fact-only events publish through an existing EventBus;
- PassiveSupervisor and visual models remain read-only;
- replay is idempotent and never replaces the record;
- non-converged deliberation is blocked before SQL;
- incompatible embeddings are blocked before Qdrant;
- GitHub mutation remains closed.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.laboratory.v1
context_contract_changed: false
external_dependencies_added: false
scheduler_created: false
scheduler_modified: false
parallel_orchestrator_created: false
parallel_eventbus_created: false
parallel_registry_created: false
sql_remains_authority: true
qdrant_projection_only: true
eventbus_observation_only: true
provider_active: true
github_mutation_performed: false
network_added: false
```
