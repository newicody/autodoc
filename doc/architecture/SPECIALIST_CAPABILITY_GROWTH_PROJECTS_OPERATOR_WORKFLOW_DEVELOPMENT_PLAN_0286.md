# Development plan — Projects operator workflow and remaining work after 0285

## Phase 0286 — expose capability growth safely in newicody/projects

1. **0286-r1 — reuse audit**: inventory and lock reuse/authority boundaries.
2. **0286-r2 — review projection contract**: immutable, non-authoritative projection of proposal, revision, decision, SQL history and Scheduler selection.
3. **0286-r3 — request form contract**: dedicated capability-growth Issue form plus normalized local intake; the form requests work but never approves it; update `INSTALLATION.md` cumulatively for the new copied form.
4. **0286-r4 — ProjectV2 fields/views**: add specialist/revision/capability/decision/SQL-reference fields and a dedicated review view; update `INSTALLATION.md` cumulatively.
5. **0286-r5 — publication plan**: one deterministic plan for append-only Issue comment plus restricted field projection.
6. **0286-r6 — operator-authorized adapter**: reuse the existing `gh` mutation boundary; preview by default, `--execute` plus exact plan digest required.
7. **0286-r7 — readback/readiness**: query-only readback, field/comment correlation and deployment readiness without mutation.
8. **0286-r8 — real closed-loop smoke**: local approved revision → controlled publication → query-only readback → correlated proof.

## Phase 0287 — multi-laboratory evidence aggregation

- audit existing visit/transfer and evidence contracts;
- aggregate evidence without merging laboratory authorities;
- retain provenance, deduplicate by digest and reject incompatible capability claims;
- operator weighting/acceptance policy;
- SQL-authoritative aggregation history;
- Scheduler selection constraints;
- passive observation and closed-loop smoke.

## Phase 0288 — bounded specialist performance evaluation

- reuse audit before adding evaluation surfaces;
- immutable evaluation datasets and run manifests;
- per-revision metrics, regression thresholds and reproducibility evidence;
- no self-promotion and no automatic authority transfer from metrics;
- operator decision, SQL history, passive observation and smoke;
- optional Projects projection through the already-controlled 0286 boundary.

## Phase 0289 — Chalouf final integrator

- create the Chalouf need from GitHub Projects;
- build contextual variants and specialist proposals;
- dispatch approved specialist revisions through the existing Scheduler;
- perform controlled laboratory visits/interventions;
- collect local/external research evidence under policy;
- compare variants and cross-validate results;
- produce human synthesis, design plan and fabrication planning;
- publish controlled status/results back to the Kanban;
- execute installation, recovery, replay and acceptance tests.

## Remaining acceptance work

- run every patch separately with compileall, `tests/rules`, focused context tests and global suite when required;
- keep `templates/github/projects-repository/INSTALLATION.md` cumulative on every useful bundle/deployment change;
- compare the bundle against the real `newicody/projects` checkout with `rsync -aivn` and never `--delete`;
- keep SQL authoritative, Qdrant non-authoritative, EventBus passive and Scheduler unique;
- replace the deterministic fake specialist/laboratory only behind existing ports, after the generic contracts and real evidence boundaries are stable.
