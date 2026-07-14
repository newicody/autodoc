# Phase 0284-r9 report — specialists/laboratories live-path evidence

## Result

`0284-r9` adds the missing immutable evidence boundary recommended by r8.
It validates one saved r7 integrated result, derives r8 operational evidence,
and delegates the final closure decision to the existing r8 source audit.

## Reuse audit

No suitable existing verifier or CLI was present for the r7/r8 operational
handoff. The new source module is limited to a pure evidence use-case. The new
CLI is justified as a thin filesystem adapter because no current command can
load an r7 JSON result plus the r8 source surfaces and emit the correlated
closure report.

## Boundaries

```text
existing_scheduler_remains_orchestrator: true
new_scheduler_added: false
new_laboratory_manager_added: false
sql_remains_authority: true
qdrant_projection_recall_only: true
eventbus_observation_only: true
github_mutation_performed: false
projectv2_mutation_performed: false
expected_e5_dimension: 384
```

The verifier itself performs no real backend execution. It can only attest a
previously produced r7 result. Therefore the patch tests are green while the
repository operational status remains `transition` until the operator supplies
a real local result and obtains `phase_0284_closed=true`.

## Tests performed in the delivery workspace

```text
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_specialists_laboratories_live_path_evidence_0284.py \
  tests/rules/test_specialists_laboratories_live_path_evidence_0284_rule.py

9 passed
```

Additional verification:

- Python compilation of all new Python files;
- deterministic digest replay;
- exact 384-dimensional gate;
- mutation evidence rejection;
- missing source surface rejection;
- deep JSON snapshot isolation;
- cumulative Projects installation guide check.

## `newicody/projects` installation guide

`templates/github/projects-repository/INSTALLATION.md` was reviewed and updated
to version `0284-r9`. The safe Copilot default remains `false`; the guide now
contains the post-installation, no-mutation evidence command.

## Code rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: the patch follows the existing immutable command/result,
thin CLI, injected IO and live-path evidence rules; no new programming
technique or backend boundary is introduced.
external_dependency_added: false
live_path_status: transition until a real operator result is verified
```

## Next patch

After a real green r9 report:

```text
0285-r1-specialist-capability-growth-reuse-audit
```
