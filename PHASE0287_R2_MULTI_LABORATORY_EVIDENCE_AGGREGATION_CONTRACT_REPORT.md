# Phase 0287-r2 — multi-laboratory evidence aggregation contract

Status: immutable contract complete.

The phase adds one canonical evidence item envelope and one deterministic
aggregate. Existing `SpecialistCapabilityEvidenceRef` values are adapted rather
than redefined. Each item keeps a content digest, claim, source, specialist and
an opaque provenance reference. The aggregate requires at least two distinct
provenance references and produces a deterministic `aggregation_digest`.

The full provenance chain remains intentionally unvalidated until r3. Duplicate
content digests remain accepted so r4 can perform explicit deduplication.
Contradiction detection, operator weighting, SQL history, Scheduler selection
and observation remain absent.

INSTALLATION.md reviewed.
No update required for 0287-r2: no workflow, Issue form, ProjectV2 field/view,
secret, variable or file deployed into `newicody/projects` changes.
