# Phase 0287-r7 — multi-laboratory evidence durable history

Status: append-only SQL-authority history contract complete.

Only approved r6 weighting decisions may be appended. Entries preserve a
`sql_ref`, contiguous sequence number and previous-entry digest. The port
enforces optimistic entry-count and head-digest checks, exact replay
idempotence and identity collision rejection.

The deterministic adapter is test-only and reports
`durable_write_performed=false`; a real SQL adapter belongs behind the port.

INSTALLATION.md reviewed.
No update required for 0287-r7: no workflow, ProjectV2 field/view, secret,
variable or Projects repository file changes.
