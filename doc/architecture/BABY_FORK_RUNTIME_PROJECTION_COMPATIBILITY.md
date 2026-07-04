# Baby-fork runtime projection compatibility

Status: corrective phase after 0066.

## Problem

The first projection adapter was structurally correct but it only looked for variants in a direct top-level field:

```text
report["variants"]
```

The real baby-fork smoke report can store variants in nested locations. This produced:

```json
"variant_count": 0
```

even when `selected_variant_id` was present.

## Fix

The projection now searches common report locations:

```text
variants
generated_variants
candidate_variants
variant_generator.variants
variant_generator.generated_variants
variant_generator_stub.variants
result.variants
final_context.variants
final_context.candidate_variants
```

It also has a recursive fallback for variant-like lists.

## Added projected fields

The `variants.generated`, `context.versioned`, `variant_stub` route event and `context_gate` patch payloads now include:

```text
variant_count
variant_ids
selected_variant_id
```

## DataHandle hash

The report `DataHandle` no longer uses the placeholder:

```text
sha256:projection
```

It now uses a deterministic SHA-256 over the canonical JSON representation of the report.

## Non-goals

This phase still does not add:

```text
real shared memory
semaphores
ring buffer
RouteProxy daemon
Scheduler wiring
ControlFS mutation
NetworkBridge
HardwareBridge
cluster dispatch
```
