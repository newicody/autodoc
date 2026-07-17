# 0285-r2 — Specialist capability growth proposal contract

This patch introduces the immutable, evidence-backed proposal boundary selected
by the 0285-r1 reuse audit.

## Scope

- add `SpecialistCapabilityEvidenceRef`;
- add `SpecialistCapabilityGrowthProposal`;
- bind evidence to `specialist_ref`, capability, source reference and SHA-256;
- keep every proposal non-authoritative and non-dispatchable;
- add context tests, architecture rules, report, documentation, DOT, changelog
  and manifest;
- review `templates/github/projects-repository/INSTALLATION.md` without changing
  it because no Projects deployment surface changes.

## Explicit non-goals

- no operator decision gate;
- no descriptor mutation or revision construction;
- no SQL/Qdrant write;
- no Scheduler modification;
- no backend, runtime, network or GitHub API call;
- no new registry or laboratory manager.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0285-r2-specialist-capability-growth-proposal-contract \
  --commit \
  --push \
  --allow-dirty
```

## Expected tests

```bash
PYTHONPATH=src:. python -m compileall -q src tests
PYTHONPATH=src:. python -m pytest -q tests/rules
```

The next planned patch is
`0285-r3-portable-specialist-revision-lineage-contract`.
