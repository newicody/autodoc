# Changelog — 0287-r7-r15-r2 imported Actions run preview

## Added

- exact read-only discovery and download of the three correlated Actions artifacts;
- pure dual-artifact preflight before real runtime initialization;
- mandatory explicit SourceCandidate `promote` or `merge` decision;
- typed imported-run/artifact/runtime/proof/plan correlation contract;
- real-runtime factory and immutable backend-attestation contracts;
- structural validation of Scheduler, SQL, projection, embedding and retrieval ports;
- explicit `tool-bounded` and `externally-managed` Scheduler lifecycle modes;
- early Scheduler failure propagation without leaving r14 blocked;
- exact checks of the two r14 OpenVINO/E5-384 + Qdrant projection receipts;
- `run_love_actions_closed_loop_0287.py` JSON producer and mandatory remote preview;
- artifact ids, content digests, run id, runtime evidence, proof digest and plan digest in one result;
- clear missing-plan error in the r15-r1 publication CLI;
- functional, tool and architecture-rule tests;
- report, architecture note, DOT and manifest.

## Removed before packaging

- deterministic adapters that could have been mistaken for real r12 projection proof;
- any default or fallback runtime selection.

## Unchanged

- Scheduler implementation and orchestration authority;
- r14 specialist, SQL, evidence and synthesis logic;
- r13 publication body and digest;
- r15-r1 mutation gates and ordering;
- GitHub Actions workflows;
- remote mutation remains disabled in r15-r2.
