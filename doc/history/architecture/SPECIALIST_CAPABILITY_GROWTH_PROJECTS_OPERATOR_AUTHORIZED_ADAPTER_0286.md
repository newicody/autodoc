# Specialist capability growth — operator-authorized Projects adapter

## Flow

```text
r5 immutable publication plan
→ preview
→ local operator approve
→ execute flag
→ exact plan_digest confirmation
→ existing Issue-comment boundary
→ existing ProjectV2 mutation boundary
→ bounded execution evidence
```

The adapter owns policy validation and composition only. Network mechanics stay
behind the existing port. A rejected, deferred, invalid, colliding or
digest-mismatched plan never reaches that port.

## Authority

- SQL is the durable authority.
- Scheduler remains the only orchestrator.
- GitHub Projects is a review/workflow projection.
- Qdrant is not authoritative.
