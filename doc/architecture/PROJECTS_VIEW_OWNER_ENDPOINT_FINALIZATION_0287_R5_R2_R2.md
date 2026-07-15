# Content-addressed ProjectV2 endpoint repair

## Why

A unified diff depends on surrounding source context. The local script and the
reconstructed fixtures differed, so repeated hunks were rejected safely.

## Final method

```text
read exact local file
→ assert numeric endpoint occurs exactly once
→ replace it with owner-login endpoint
→ write file
→ apply documentation-only patch
→ run all rules
→ commit both changes together
```

The resulting endpoint is:

```python
views_endpoint = (
    f"users/{plan.owner}/projectsV2/{plan.number}/views"
)
```

The numeric `user_id` remains available in the plan report for diagnostics.
