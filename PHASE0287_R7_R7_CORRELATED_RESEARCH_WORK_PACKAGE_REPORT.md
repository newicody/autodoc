# Phase 0287-r7-r7 — correlated research work package

## Objective

Close the read-only GitHub ingress into one immutable package that can later be
routed by the existing Scheduler to a concrete laboratory.

The phase reuses:

- `github_dual_artifact_run_assembly_0281.py` for run grouping;
- `github_dual_artifact_source_candidate_intake_0275.py` for semantic intake;
- `github_issue_attachment_manifest.py` for Issue attachment references;
- `github_attachment_reference_fetch.py` for server-dataset fetch evidence.

No new fetcher, queue, Scheduler, laboratory provider or storage path is added.

## Contract

`missipy.research.correlated_work_package.v1` contains:

- source repository, Issue, run, frame and revision identities;
- the authoritative request in its original public schema;
- the correlation manifest in its original public schema;
- the optional Copilot advisory in its original v1 or v2 schema;
- the `SourceCandidate` reference;
- conversation, return-route and context-generation identities;
- explicit context and evidence references;
- fetched attachment dataset references, digests, kinds and byte counts.

The package never embeds attachment bytes or exposes server-local paths.

## Validation

The builder fails closed when:

- run assembly or intake is invalid;
- an authority or mutation boundary changes;
- repository, Issue, frame or revision identities diverge;
- request/advisory/manifest references diverge;
- an advisory schema is unknown or claims authority;
- an attachment is referenced but not fetched;
- a fetch report contains an unlisted attachment;
- an attachment digest or expected digest is invalid.

## Authority and execution boundaries

```text
request artifact        = authoritative content
Copilot advisory        = hint only
attachment bytes        = server dataset, referenced only
work-package builder    = pure/read-only
Scheduler route         = not created in this phase
SQL/Qdrant writes       = not performed
GitHub mutation         = not performed
```

## Closure

The GitHub run can now be represented as one deterministic research package.
The next phase versions the existing specialist/laboratory message contract and
defines a generic deep-analysis contribution carried by this package.

code_rule_review: done
code_rule_update_required: false
live_path_status: contract_ready
installation_update_required: false
