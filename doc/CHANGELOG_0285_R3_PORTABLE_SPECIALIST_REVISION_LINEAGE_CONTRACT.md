# Changelog — 0285-r3 portable specialist revision lineage contract

- Added immutable `PortableSpecialistRevision` contract.
- Added append-only `SpecialistRevisionLineage` contract.
- Reused the existing `PortableSpecialistDescriptor` as the descriptor snapshot.
- Locked stable specialist identity, contiguous revision numbering and linear parent
  continuity.
- Added deterministic descriptor, revision and lineage SHA-256 digests.
- Added pure correlation validation against the existing r2 proposal contract.
- Kept operator approval, SQL persistence, Scheduler selection and runtime execution
  outside this phase.
- Reviewed the cumulative `newicody/projects` installation guide; no update was
  required.
