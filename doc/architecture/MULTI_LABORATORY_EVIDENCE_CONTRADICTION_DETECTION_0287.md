# Multi-laboratory evidence contradiction detection

## Input

```text
r4 valid deduplication result
+ explicit contradiction policy
```

## Detected cases

```text
same key + same value + supports/opposes
same key + different positive values + exclusive claim key
same key + policy-declared exclusive value pair
same content digest + incompatible interpretation of the same key
```

The detector does not infer contradictions between unrelated claim keys.
Contradictions are deterministic, digest-bound and remain `unresolved`.

## Output boundary

```text
contradiction_detection_performed = true
ready_for_operator_weighting       = true
weighting_authorized               = false
durable_state_written              = false
scheduler_selection_allowed        = false
```

R6 will define the explicit operator weighting decision. SQL remains the
durable authority and Scheduler remains the only orchestrator.
