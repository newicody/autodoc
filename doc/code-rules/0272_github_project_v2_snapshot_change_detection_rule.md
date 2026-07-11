# Rule 0272-r4 — ProjectV2 snapshot change detection

1. Change detection consumes only immutable 0272-r3 snapshots.
2. It must not contact GitHub or require a token.
3. It must not perform GraphQL query or mutation operations.
4. It must not write SQL, Qdrant, EventBus or SHM.
5. It must compare only snapshots belonging to the same ProjectV2 identity.
6. Change sets are immutable, serializable and content-addressed.
7. Existing snapshots and change sets are never deleted or overwritten with different content.
8. A single snapshot is a valid baseline, not a synthetic remote change.
9. Effects remain in the CLI boundary; the core module remains pure.
