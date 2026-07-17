# Phase 0287-r7-r15-r3-r11-r2 — Controlled SQL projection seed

## Result

This unit adds a deterministic, preview-first SQL-only bootstrap for the first
live projection probe. It creates one immutable authority object and one
accepted child revision. The existing `context-revision:love-base` revision is
used as parent and is never modified.

The dedicated CLI is justified because combining SQL-authority bootstrap writes
with the existing Qdrant point-write probe would merge two independently gated
effect boundaries. The CLI remains a thin transitional operator adapter.

## Idempotence

Both writes reuse the immutable authority methods already present:

- `put_object`;
- `put_revision`.

An identical replay is accepted. Any immutable collision fails before the seed
is executed. A process interruption after the object write can be recovered by
replaying the same confirmed plan; the child revision is then completed.

## Locked boundaries

- PostgreSQL is the only backend written;
- the base revision is immutable and unchanged;
- no Qdrant client is constructed;
- no Qdrant point is written;
- no OpenVINO runtime is constructed;
- no Scheduler is constructed;
- no secret or authority body appears in the execution receipt.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing typed command/use-case, explicit gate, immutable result and IO-boundary rules are sufficient
live_path_status: transition
live_path_uses_real_backend: true
context_contract_version: missipy.context.authority_object.v1 + missipy.context.revision.v1
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```

## Next proof

Run preview, confirm its digest, execute the SQL seed, then use the returned
`object_ref` and `revision_ref` with the already-integrated live projection
probe.
