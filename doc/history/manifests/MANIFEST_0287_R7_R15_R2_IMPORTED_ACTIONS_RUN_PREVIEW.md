# Manifest — 0287-r7-r15-r2 imported Actions run preview

## Added files

- `src/context/love_imported_actions_runtime_contract_0287.py`
- `src/context/love_imported_actions_run_preview_0287.py`
- `tools/run_love_actions_closed_loop_0287.py`
- `tests/context/test_love_imported_actions_runtime_contract_0287_r7_r15_r2.py`
- `tests/context/test_love_imported_actions_run_preview_0287_r7_r15_r2.py`
- `tests/tools/test_run_love_actions_closed_loop_0287_r7_r15_r2.py`
- `tests/rules/test_love_imported_actions_run_preview_0287_r7_r15_r2_rule.py`
- `PHASE0287_R7_R15_R2_IMPORTED_ACTIONS_RUN_PREVIEW_REPORT.md`
- `doc/architecture/IMPORTED_ACTIONS_RUN_PREVIEW_0287_R7_R15_R2.md`
- `doc/architecture/IMPORTED_ACTIONS_RUN_PREVIEW_0287_R7_R15_R2.dot`
- `doc/CHANGELOG_0287_R7_R15_R2_IMPORTED_ACTIONS_RUN_PREVIEW.md`
- `doc/manifests/MANIFEST_0287_R7_R15_R2_IMPORTED_ACTIONS_RUN_PREVIEW.md`

## Modified files

- `tools/publish_love_final_deliverable_0287.py`
  - report absent/invalid plan files without traceback;
  - point the operator to the r15-r2 producer.

## Invariants

- Preview remains mandatory and is performed automatically.
- Exactly three non-expired Actions artifacts from the requested run are accepted.
- Their existing intake/correlation contract is validated before runtime initialization.
- The SourceCandidate decision is explicit: `promote` or `merge`.
- Artifact ids, content digests, run id, runtime evidence, proof digest and plan digest remain correlated.
- The output remains directly consumable by the r15-r1 publisher.
- No remote mutation can occur in the r15-r2 command.
- Scheduler is injected, reused and not modified. `tool-bounded` owns a dedicated
  `run()`/`shutdown()` window; `externally-managed` never steals the server loop.
- No dummy runtime or fallback can satisfy the real r12 projection proof.
- E5 dimension remains exactly 384 and Qdrant remains reference-only projection/recall.
- No dependency, SVG or binary file is added.

## Roadmap

- `0287-r7-r15-r3`: bind the factory to the concrete server deployment, run the mandatory preview, perform controlled remote publication, verify exact Issue/ProjectV2 readback and record replay evidence;
- `0287-r7-r16`: recovery, installation and prototype closure.

## Corrective continuation

`0287-r7-r15-r2-r1` removes the need to provide ProjectV2 node identifiers and
the runtime factory reference on every command. Exact resolution and the
mandatory preview remain unchanged.
