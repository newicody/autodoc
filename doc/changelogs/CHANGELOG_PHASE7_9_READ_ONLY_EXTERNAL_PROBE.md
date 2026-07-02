# Changelog — Phase 7.9 Read-Only External Probe

## Added

- `src/context/source_candidate_read_only_external_probe.py`
  - Builds read-only probe requests from operator external review reports.
  - Defines a probe adapter protocol.
  - Adds a fake local probe adapter.
  - Writes and renders probe results.

- `tests/context/test_source_candidate_read_only_external_probe.py`
  - Covers request building, readiness checks, fake probe behavior, JSON IO and rendering.

- `tests/rules/test_source_candidate_read_only_external_probe_rule.py`
  - Ensures the probe remains fake-only, local and network-free.

- `doc/docs/architecture/context/65_source_candidate_read_only_external_probe.dot`
  - Documents the read-only external probe boundary.

## Not added

- No real external adapter.
- No external API calls.
- No network.
- No token handling.
- No remote mutation.
- No Scheduler change.
