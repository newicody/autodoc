# Multi-laboratory evidence operator weighting policy

## Flow

```text
r5 contradiction detection
+ operator identity
+ policy
+ canonical evidence weights
+ contradiction dispositions
→ approve / reject / defer
→ weighting_digest
```

Weights use integer basis points. The default approved total is 10,000.

## Contradiction dispositions

```text
prefer_left
prefer_right
retain_both
exclude_both
defer
```

The disposition must agree with the assigned canonical weights. A
same-canonical contradiction cannot prefer one side because both sides resolve
to the same content identity.

## Authority boundary

```text
explicit_operator_authority      = true
weighting_authorized             = approve
durable_history_append_allowed   = approve
durable_state_written            = false
contradiction_resolution_performed = false
scheduler_selection_allowed      = false
```

R7 may persist the approved decision under SQL authority. Scheduler selection
remains a later r8 responsibility.
