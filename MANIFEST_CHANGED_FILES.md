# Manifest — Phase 5.14 — SourceCandidate local contract

Changed files included in this archive:

```text
README.md
MANIFEST_CHANGED_FILES.md
PHASE5_14_TEST_REPORT.md
doc/SOURCE_CANDIDATE_CONTRACT.md
doc/CHANGELOG_PHASE5_14_SOURCE_CANDIDATE_CONTRACT.md
doc/docs/architecture/00_global.dot
doc/docs/architecture/context/37_local_context_loop_cli.dot
doc/docs/architecture/context/38_source_candidate_contract.dot
src/context/__init__.py
src/context/local_context_loop_cli.py
src/context/source_candidate.py
tests/context/test_source_candidate.py
```

Notes:

- `src/context/local_context_loop_cli.py` is included only for a Phase 5.13 hygiene fix: duplicate `_write_report` header collapsed to a single definition.
- No SVG files are included.
- No `__pycache__` files are included.
- No patch script is included.
