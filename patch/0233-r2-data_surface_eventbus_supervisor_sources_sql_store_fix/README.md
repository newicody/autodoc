# 0233-r2 — data surface EventBus supervisor sources SQL_STORE fix

Apply this follow-up on top of the worktree where 0233-r1 was applied but the
full suite failed on `test_data_surface_helpers_cover_planned_sources`.

The fix is intentionally small: the data-surface cell-kind allowlist now accepts
`SQL_STORE`, which is the canonical kind emitted by `sql_supervision_event(...)`.
