# Changelog 0283-r4-r1 — normalized vector fixture fix

- Replaced the invalid all-zero projection fixture with a real unit vector.
- Preserved dimension 384 and the existing `normalized=true` expectation.
- Added a rule preventing the all-zero fixture from returning.
- Kept the runtime normalization guard unchanged.

```text
runtime_source_modified: false
fixture_only_fix: true
projection_binding_logic_modified: false
qdrant_write_performed: false
qdrant_search_performed: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```
