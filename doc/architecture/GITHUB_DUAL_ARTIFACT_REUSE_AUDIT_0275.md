# GitHub dual-artifact reuse audit — 0275-r1

## Decision

The repository already owns the reusable boundaries required for the next
GitHub exchange:

- `github_action_ticket_artifact.py` defines an authoritative ticket artifact;
- `github_project_push_frame.py` defines an advisory-only Copilot opinion;
- `autodoc-ticket-artifact.yml` and its builder already publish separate files;
- `github_actions_artifact_scan_once_live_0272.py` is the read-only fetch path;
- `SourceCandidate` and the 0272 gate own local operator decisions;
- `github_publication_review.py` owns local review before remote publication;
- `source_candidate_remote_mutation_gate.py` is closed by default;
- `source_candidate_github_adapter.py` currently provides a fake-only adapter.

No global GitHub manager, client, Scheduler, bus or registry is needed.

## Missing seams

1. A strict physical dual-artifact v1 contract and linking manifest.
2. A producer workflow that can invoke Copilot CLI advisory-only.
3. A local intake that builds SourceCandidate exclusively from the request.
4. A smoke from dual artifacts to the existing laboratory loop.
5. A controlled publication command and real transport membrane.
6. A remote revision/idempotency guard before apply.

## Locked authority rule

The request artifact is authoritative. Copilot output is advisory evidence only.
The advisory may never replace request title/body, authorize intake, choose the
SourceCandidate decision or open remote mutation.

## Planned sequence

- 0275-r2: contracts and manifest;
- 0275-r3: Actions producer and optional Copilot CLI advisory;
- 0275-r4: read-only local intake;
- 0275-r5: dual-artifact to laboratory smoke;
- 0276-r1: mutation boundary audit;
- 0276-r2: controlled publication contract;
- 0276-r3: injected real GitHub transport adapter;
- 0276-r4: collision, revision and idempotency guard.
