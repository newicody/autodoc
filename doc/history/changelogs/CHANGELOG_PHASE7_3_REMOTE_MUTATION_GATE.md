# Changelog — Phase 7.3 Remote Mutation Gate

## Added

- `src/context/source_candidate_remote_mutation_gate.py`
  - Validates future remote write eligibility from a GitHub projection dry-run payload.
  - Blocks by default.
  - Requires explicit policy enablement, operator confirmation and repository allowlist.
  - Can require projection permission, dry-run payloads and no safety flags.
  - Writes a local gate result artifact.

- `tests/context/test_source_candidate_remote_mutation_gate.py`
  - Covers default blocking, explicit pass policy, allowlist rejection, projection denial, safety flag blocking, file IO and rendering.

- `tests/rules/test_source_candidate_remote_mutation_gate_rule.py`
  - Ensures the gate stays closed by default and has no network/process calls.

- `doc/docs/architecture/context/61_source_candidate_remote_mutation_gate.dot`
  - Documents the remote mutation gate boundary.

## Not added

- No GitHub API calls.
- No network.
- No token handling.
- No remote mutation.
- No adapter apply.
- No Scheduler change.
