# Production prototype smoke composition - 0269

## Intent

0269 provides one operator command that composes the existing phase tools:

```text
0260 -> 0261 -> 0262 -> 0263 -> 0264 -> 0265 -> 0266 -> 0267 -> 0268
```

It does not replace those tools and does not create a RuntimeManager. The typed
core only builds a deterministic plan and folds injected step outcomes. The CLI
adapter is the sole process boundary and invokes the existing Python tools in
order.

## Existing surface audit

The repository already contains `tools/run_p1_closed_loop_operator_smoke.py`,
which is retained as the earlier 0145/0148/0151 composition. It cannot be
extended cleanly for 0260-0268 because its inputs and result contract belong to
the earlier P1 path.

0269 therefore adds one narrowly scoped composition contract and one CLI. It
reuses all nine existing phase tools and does not reimplement SQL persistence,
OpenVINO embedding, Qdrant projection/recall, ResultFrame composition, EventBus
observation, PassiveSupervisor observation, GitHub handoff, or OpenRC readiness.

## Modes

Plan mode is the default. It validates and serialises the nine-step command plan
without executing any phase tool.

Execute mode requires an explicit `policy_decision_id`. The current 0262 and
0263 tools expose only injected demo Qdrant executors, so 0269 also requires the
explicit `--demo-qdrant` flag until a controlled real Qdrant executor exists.
OpenVINO remains real by default; `--demo-embedding` is an explicit test mode.
The in-memory EventBus publish is also opt-in through `--demo-eventbus`; the
default still builds the observation-only facts without implicitly selecting a
demo publisher.

## Boundary

- Scheduler remains the Autodoc orchestration authority.
- Scheduler does not start PostgreSQL, Qdrant, or OpenVINO.
- OpenRC/OS/admin remains process authority for external services.
- EventBus remains observation only.
- PassiveSupervisor remains read only.
- GitHub remains a review/workflow surface and no remote mutation is allowed.
- 0269 never calls `rc-service` or `rc-update`.
- 0269 does not modify `Scheduler.run()`.

## Output

The report schema is:

```text
autodoc.production_prototype_smoke_composition.v1
```

It records the plan, each subprocess outcome, report validity, propagated
references, boundary checks, and a final valid/invalid decision. Execute mode
closes only when `sql_ref`, `embedding_ref`, `handoff_ref`, and `readiness_ref`
are present and the observation/readiness/no-mutation/no-service-start checks
have their required values.

## Next step

0270 consolidates the canonical documentation, runtime graph, manifests,
changelogs, and operational roadmap after the complete prototype smoke is green.
