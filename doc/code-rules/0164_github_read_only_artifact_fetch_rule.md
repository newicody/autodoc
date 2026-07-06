# Code rule — 0164 GitHub read-only artifact fetch

## Rule

Do not create a new GitHub adapter for 0164.

Use the existing read-only probe and projection surfaces:

- `SourceCandidateReadOnlyExternalProbeRequest`
- `FakeSourceCandidateReadOnlyExternalProbeAdapter`
- `SourceCandidateExternalProbeBundle`
- `SourceCandidateExternalProjectionContract`
- `SourceCandidateGithubProjectionPayload`
- `SourceCandidateRemoteMutationGatePolicy`
- `run_source_candidate_remote_mutation_gate`

## Required behavior

- Use the existing read-only probe.
- Use the existing external probe bundle.
- Use the existing external projection contract.
- Use the existing GitHub projection payload.
- Use the existing remote mutation gate.
- Keep the remote mutation gate closed.

## Forbidden behavior

- No remote mutation.
- No GitHub API call.
- No external network.
- No SQL write.
- No Qdrant write.
- No Scheduler execution.
- No LLM execution.
- No OpenVINO execution.
- No ingestion of the Autodoc/MissiPy development repository as an idea source.

## Repository boundary

The external repository must be explicit and must not equal the development
repository.
