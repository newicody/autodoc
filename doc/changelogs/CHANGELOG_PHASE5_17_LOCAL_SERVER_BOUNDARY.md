# Changelog — Phase 5.17 — Local server boundary

## Added

- `src/context/local_server_boundary.py`
- `tests/context/test_local_server_boundary.py`
- `doc/LOCAL_SERVER_BOUNDARY.md`
- `doc/docs/architecture/context/41_local_server_boundary.dot`

## Updated

- `src/context/__init__.py`
- `doc/docs/architecture/00_global.dot`
- `doc/docs/architecture/context/40_github_projection_design.dot`

## Notes

- The phase is contract-only.
- No HTTP server is implemented.
- No external dependency is introduced.
- No socket, daemon, watcher, network, GitHub API, token, Qdrant, LLM or OpenVINO execution is introduced.

## code_rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.17 adds a pure local server boundary contract without implementing IO or adding dependencies; no programming rule update is required.
```
