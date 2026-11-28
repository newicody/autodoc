# Correlated research work package

## Flow

```text
GitHub Actions run members
  -> 0281 run assembly
  -> 0275 semantic intake
       -> authoritative request
       -> optional Copilot advisory v1/v2
       -> SourceCandidate
  + Issue attachment manifest
  + attachment fetch report
  -> strict correlation
  -> missipy.research.correlated_work_package.v1
  -> later Scheduler-owned laboratory route
```

## Package boundary

The package transports stable identities, public artifact mappings, dataset
references and digests. It does not transport raw attachment bytes and does not
expose server-local paths to specialists.

## Reuse decision

The package is a composition contract over existing ingress surfaces. It does
not replace run assembly, intake, attachment parsing or attachment fetching.
