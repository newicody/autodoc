# Changelog — Phase 5.13 — Local context loop CLI

## Added

- Added `src/context/local_context_loop_cli.py`.
- Added a thin manual CLI boundary:
  - `python -m context.local_context_loop_cli ARTIFACT_DIR`
  - `--format text|json`
  - `--report-file FILE`
  - `--next-action inspect|relaunch|reject|archive|promote|merge`
- Added `LocalContextLoopCommand`, `LocalContextLoopResult` and CLI policies.
- Added tests for text/json rendering, report writing, ready requirement, missing artifact directory and CLI export hygiene.
- Added architecture DOT `doc/docs/architecture/context/37_local_context_loop_cli.dot`.

## Preserved boundaries

- No E5/OpenVINO execution is triggered.
- No Scheduler living loop is started.
- No daemon, server, watcher, network, GitHub API, token, Qdrant, LLM or persistent storage is introduced.
- `--next-action` is recorded only in the CLI payload; no decision is applied in Phase 5.13.

## Dependency policy

No non-stdlib Python dependency was added.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.13 ajoute une CLI manuelle mince au-dessus des contrats existants ; aucune règle de programmation nouvelle n'est nécessaire.
```
