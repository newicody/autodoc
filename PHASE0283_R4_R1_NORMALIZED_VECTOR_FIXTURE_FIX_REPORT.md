# Phase 0283-r4-r1 report — normalized vector fixture fix

## Diagnosis

The 0283-r4 runtime correctly delegates vector validation to the existing
Qdrant projection adapter. The test fixture declared `normalized=true` while
supplying 384 zero values. Its actual L2 norm was therefore zero and the
existing adapter correctly rejected it.

The fixture now supplies one unit component followed by 383 zero components:

```text
[1.0] + [0.0] * 383
```

Its dimension remains 384 and its L2 norm is exactly one.

## Impact

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

No production validation is weakened and no exception is added around the
normalization guard.
