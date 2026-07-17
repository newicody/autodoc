# Phase 0287-r7-r15-r2 — Imported Actions run to mandatory publication preview

## Objective

Connect one completed GitHub Actions run to the already-closed r14 composition
and the r15-r1 remote publication preview:

```text
completed workflow run metadata
→ exact three-artifact discovery
→ read-only artifact download
→ pure dual-artifact preflight validation
→ explicit SourceCandidate promote/merge decision
→ configured existing-runtime factory
→ real Scheduler + SQL + OpenVINO/E5 + Qdrant ports
→ r14 execution
→ reusable love-r14-result-<RUN_ID>.json
→ r15-r1 Issue + ProjectV2 preview
→ exact run/artifact/runtime/proof/plan correlation
```

No Issue comment or ProjectV2 mutation is performed.

## User-visible correction

The former example path `/tmp/love-r14-result.json` was not produced by any
command. This phase adds the missing producer and changes the publication CLI so
an absent plan file returns an explicit operator-facing error instead of a Python
traceback.

## Reuse audit

The phase reuses:

- `GitHubDualArtifactRunMember` and the r14 three-artifact assembler;
- `LoveFullDeterministicLocalSmokeCommand` and its complete r14 composition;
- `LoveFinalDeliverableRemotePublicationCommand` in preview mode;
- `GitHubCliFinalDeliverablePublicationAdapter` for remote reads only;
- the Scheduler, SQL authority, OpenVINO/E5, Qdrant projection and hybrid recall
  ports supplied by an existing runtime factory;
- the existing dual-artifact run assembler as a pure preflight before real
  runtime initialization.

The new Actions adapter uses the already accepted `gh` CLI subprocess boundary.
It does not add another HTTP client or GitHub SDK.

## Runtime truthfulness correction

A first draft used deterministic adapters while setting the r12 projection flags
`openvino_e5_used` and `qdrant_write_performed`. That would have contradicted the
r12 contract, which requires real E5 projection proof. The draft was rejected
before packaging.

The final patch contains no fake runtime. Since 0287-r7-r15-r2-r1, the
`module:function` reference is loaded from the one-time local configuration by
default; `--runtime-factory` is an advanced override. The factory must return `ImportedActionsRuntimePorts` with:

- the existing Scheduler and dispatcher with one explicit lifecycle mode:
  `tool-bounded` lets the CLI run and stop that dedicated canonical Scheduler,
  while `externally-managed` forbids the CLI from calling either `run()` or
  `shutdown()` on a server-owned loop;
- an initialized SQL authority containing the base revision;
- a projection port that performs real OpenVINO/E5-384 and Qdrant writes;
- the canonical collection, query embedder and hybrid executor;
- an immutable real-backend attestation and evidence references.

The command then cross-checks the generated r14 projection receipts:

```text
2 projection receipts
openvino_e5_used = true
qdrant_write_performed = true
dimension = 384
normalized = true
collection_name = attested Qdrant collection
```

There is no fallback factory. Missing or invalid real ports fail before the r14
JSON is written.

## Preview policy

Preview remains mandatory. `run_love_actions_closed_loop_0287.py` always:

1. imports the current successful Actions run and its exact three artifacts;
2. validates their correlation before any real backend is initialized;
3. requires the operator to choose `promote` or `merge`;
4. executes r14 only through the configured explicit real runtime factory;
5. reads current Issue comments and ProjectV2 value;
6. computes create/update/replay/collision through r15-r1;
7. writes the exact r14 JSON, runtime attestation and `plan_digest`;
8. performs no remote mutation.

The separate `publish_love_final_deliverable_0287.py --execute` command remains
the only mutation boundary and still requires the three locks plus exact digest.

## Runtime factory signature

```python
def build_runtime(
    *,
    repository: str,
    run_id: str,
    request_payload: Mapping[str, Any],
    runtime_context: Mapping[str, Any],
    created_at: str,
) -> ImportedActionsRuntimePorts:
    ...
```

This phase defines and validates the portable boundary. The corrective
0287-r7-r15-r2-r1 patch resolves ProjectV2 identities automatically and loads
the installation-owned factory reference from local configuration; it still
does not invent a second runtime manager or guess deployment paths.

## Failure modes

The command fails closed on:

- run not completed successfully;
- missing, duplicate, expired or invalid artifact identity;
- unexpected artifact filename or duplicate downloaded member;
- invalid authoritative request or dual-artifact correlation;
- missing explicit candidate decision or merge target;
- malformed or unavailable runtime factory reference;
- Scheduler lifecycle mismatch or early Scheduler failure;
- dummy, non-384, non-Qdrant or unattested runtime ports;
- r14 projection receipt/attestation mismatch;
- invalid r15-r1 preview;
- run id, repository, proof digest or plan digest mismatch;
- local output write failure.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing typed composition and real-backend evidence rules are sufficient
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: true
github_api_added: true
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```

`live_path_uses_real_backend: false` describes the patch validation environment:
no live factory was invoked while packaging. A generated result may state
`real-backend-preview` only after the mandatory runtime attestation and r14
receipt checks pass.

The CLI is justified because the existing publication CLI owns mutation and
must not also own Actions import plus runtime composition. Domain contracts stay
in `src/context`; the CLI only owns arguments, dynamic factory loading, `gh`,
files, port composition and rendering.

## Validation

Tests cover runtime attestation, structural port validation, rejection of dummy
or 385-dimensional backends, exact artifact selection and run identity, unique
extraction, pure artifact preflight, explicit candidate decision, both Scheduler
lifecycle modes, early Scheduler failure, run/plan/projection correlation,
preview-only enforcement, digest mismatch, factory reference loading and the
missing-plan error path.

## Next phase

`0287-r7-r15-r3 — live Issue and ProjectV2 closed-loop evidence` must bind this
factory contract to the server's concrete existing OpenVINO/Qdrant deployment,
execute the mandatory preview against `newicody/projects`, obtain operator
approval, publish with the exact digest, verify remote readback and prove replay
without a new mutation.
