# GitHub dual-artifact run assembly contract — 0281-r2

## Purpose

The GitHub Actions workflow now produces three physically separate artifacts:

```text
autodoc-authoritative-request/authoritative_request.json
autodoc-copilot-advisory/copilot_advisory.json
autodoc-dual-artifact-manifest/dual_artifact_manifest.json
```

The generic fetcher downloads artifacts individually. This phase adds the pure,
run-level contract needed to correlate those already-downloaded members before
the fetcher integration phase.

## Reuse audit

The existing 0275 intake already owns semantic validation of:

- authoritative request schema and locked authority flags;
- optional Copilot advisory schema and non-authority flags;
- request/advisory/manifest correlation identifiers;
- request and advisory SHA-256 digests;
- SourceCandidate creation from authoritative content only.

Therefore 0281-r2 does not duplicate this logic. It selects one request, one
optional advisory and one manifest, then delegates to
`run_github_dual_artifact_source_candidate_intake`.

A new module is justified because no existing surface represents an immutable
GitHub Actions run-level group. It is a local use-case contract, not a manager,
registry, worker, scheduler, bus, network adapter or filesystem adapter.

## Boundaries

```text
input = already-downloaded artifact members
output = immutable correlation/intake result
network = forbidden
filesystem write = forbidden
Scheduler route = forbidden
SQL write = forbidden
Qdrant write = forbidden
GitHub mutation = forbidden
```

The complete Copilot advisory remains present under `result.intake.advisory` for
future operator and laboratory context. It remains consultative and is never
copied into authoritative SourceCandidate title/body state.

## Repository deployment impact

```text
newicody/autodoc: modified by this patch
newicody/projects: no modification required
```

The external workflow already emits the three expected artifact names and
filenames. Workflow caching belongs to the later 0281-r4 patch.
