# Phase 0287-r4 — multi-laboratory evidence digest deduplication

Status: immutable deduplication proof complete.

The phase validates the r3 provenance chain, groups evidence by the existing
content SHA-256, selects the lexicographically first evidence reference as the
canonical alias and preserves every original item, provenance, source,
laboratory and specialist reference.

A SHA-256 of each `source_ref` is included as a deterministic source-identity
digest. Same-content evidence from different sources or laboratories remains
visible as corroboration. Different claim interpretations attached to the same
content digest are retained and flagged for r5 rather than erased.

The targeted tests also corrected the r3 typed-reference regex, which had
accidentally rejected payloads beginning with `s` such as `result:shared`.

Contradiction detection, operator weighting, SQL history, Scheduler selection
and passive observation remain outside r4.

INSTALLATION.md reviewed.
No update required for 0287-r4: no workflow, Issue form, ProjectV2 field/view,
secret, variable or file deployed into `newicody/projects` changes.
