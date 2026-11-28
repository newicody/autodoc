# Documentation refresh policy — 0154

The repository now contains many historical phase documents. The current documentation policy is:

1. Preserve historical phase docs. They explain why a boundary was introduced.
2. Add current-state index pages for the active architecture.
3. Add summary DOT graphs rather than deleting phase graphs.
4. Keep hierarchy stable:
   - `doc/architecture` for narrative architecture.
   - `doc/code-rules` for enforceable rules.
   - `doc/docs/architecture/runtime` for DOT graphs.
   - `doc/manifests` for patch manifests.
5. Avoid live-runtime constructor signatures in rule/docs text when a rule forbids those exact strings. Use descriptive wording instead.
6. Re-run `tools/audit_architecture_docs_and_surfaces.py` before broad documentation rewrites.

## Canonical current-state pages

- `doc/architecture/CURRENT_ARCHITECTURE_STATE_0154.md`
- `doc/architecture/P1_TO_P5_ROADMAP_0154.md`
- `doc/architecture/DOC_REFRESH_POLICY_0154.md`

## Canonical current-state graphs

- `doc/docs/architecture/runtime/154_current_p1_pipeline.dot`
- `doc/docs/architecture/runtime/154_p1_to_p5_roadmap.dot`
