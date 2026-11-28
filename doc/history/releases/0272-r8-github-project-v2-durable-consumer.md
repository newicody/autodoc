# 0272-r8 — ProjectV2 durable consumer

This release consumes an approved immutable r7 gate record into the existing SQL
context authority. It preserves idempotence, performs mandatory SQL readback and
keeps OpenVINO, Qdrant, GitHub mutation, Scheduler and SHM boundaries closed.

The durable record is intentionally laboratory-neutral. Vector compatibility is
reserved for 0272-r9; laboratory reuse audit is reserved for 0273-r1.
