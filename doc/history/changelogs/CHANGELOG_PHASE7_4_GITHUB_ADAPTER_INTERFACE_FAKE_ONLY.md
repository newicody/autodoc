# Changelog — Phase 7.4 GitHub Adapter Interface Fake-Only

## Added

- `src/context/source_candidate_github_adapter.py`
  - Defines a GitHub projection adapter protocol.
  - Adds a fake local adapter.
  - Routes dry-run/apply through the remote mutation gate.
  - Records local fake apply simulations only when the gate passes.

- `tests/context/test_source_candidate_github_adapter.py`
  - Covers protocol shape, dry-run gate integration, blocked apply, passing fake apply and serialization.

- `tests/rules/test_source_candidate_github_adapter_rule.py`
  - Ensures the adapter remains fake-only, network-free and Scheduler-free.

- `doc/docs/architecture/context/62_source_candidate_github_adapter_interface.dot`
  - Documents the fake-only adapter boundary.

## Not added

- No real GitHub adapter.
- No GitHub API calls.
- No network.
- No token handling.
- No remote mutation.
- No Scheduler change.
