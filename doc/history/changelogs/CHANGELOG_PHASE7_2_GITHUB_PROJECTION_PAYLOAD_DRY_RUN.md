# Changelog — Phase 7.2 GitHub Projection Payload Dry-Run

## Added

- `src/context/source_candidate_github_projection_payload.py`
  - Builds a local GitHub-shaped projection payload from the generic external projection contract.
  - Preserves dry-run and no-remote-mutation semantics.
  - Converts SourceCandidate items to issue creation intents.
  - Preserves safety flags as labels.

- `tests/context/test_source_candidate_github_projection_payload.py`
  - Covers allowed payloads, blocked contracts, safety labels, terminal items, JSON IO and invalid policy.

- `tests/rules/test_source_candidate_github_projection_payload_rule.py`
  - Ensures the payload builder stays dry-run only and has no network/process calls.

- `doc/docs/architecture/context/60_source_candidate_github_projection_payload.dot`
  - Documents the GitHub-shaped dry-run boundary.

## Not added

- No GitHub API calls.
- No network.
- No remote mutation.
- No token handling.
- No adapter apply.
- No Scheduler change.
