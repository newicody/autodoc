# Changelog 0287-r2

- add immutable `MultiLaboratoryEvidenceItem`;
- add immutable `MultiLaboratoryEvidenceAggregate`;
- reuse `SpecialistCapabilityEvidenceRef` through a pure adapter;
- add deterministic item and aggregation digests;
- require two distinct opaque provenance references;
- preserve duplicate content digests for explicit r4 handling;
- keep provenance validation, contradictions, weighting, storage and selection out of r2;
- make the r1 audit progression rule cumulative.
