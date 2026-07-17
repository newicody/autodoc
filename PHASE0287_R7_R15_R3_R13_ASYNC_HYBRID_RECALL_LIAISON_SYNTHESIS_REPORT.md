# Phase 0287-r7-r15-r3-r13 — Async hybrid recall and liaison synthesis

## Result

The r12 result is now continued without reprojecting either specialist output.
The query embedding is awaited through the existing async E5 adapter, dense and
sparse candidates are retrieved through the existing hybrid composition, and
both SQL authority objects must be rehydrated before synthesis can proceed.

The synchronous legacy composition and the asynchronous live composition now
share one finalization function for mutualization, liaison synthesis, final
artifact construction and immutable synthesis revision persistence.

## Locked boundaries

- the two r12 projection receipts are reused unchanged;
- no Qdrant point is written in r13;
- SQL rehydration of both specialist analyses is mandatory;
- one-laboratory mutualization remains distinct from multi-laboratory validation;
- no Scheduler, event loop, backend, manager or publication surface is created.
