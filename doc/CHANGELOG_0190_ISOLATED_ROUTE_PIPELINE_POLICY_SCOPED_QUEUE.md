# Changelog — 0190 Isolated route pipeline policy-scoped queue

## Added

- Fresh `scheduler.route_requests.policy_scoped.jsonl` derived from the
  append-only queue and filtered by current `policy_decision_id`.
- `policy_scoped_queued_count` in the consolidated 0189 pipeline report.
- Test covering repeated runs with previous queue entries.

## Changed

- 0189 downstream stages now consume the policy-scoped queue instead of the full
  append-only queue.

## Not changed

- No new runtime handler.
- No Scheduler.run modification.
- No production route write.
