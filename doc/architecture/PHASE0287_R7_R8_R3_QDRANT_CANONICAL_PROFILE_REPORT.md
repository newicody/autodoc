# Phase 0287-r7-r8-r3 — Qdrant canonical profile report

## Status

Implemented as an inspection-only contract.

## Reuse audit

The patch reuses:

- `missipy.embedding_space_profile.v1` from the existing ProjectV2 E5
  projection path;
- `missipy.context.vector_projection_metadata.v1` from r8-r2 SQL authority;
- the existing Scheduler-managed OpenVINO/E5 and Qdrant execution surfaces.

It does not create a second Qdrant executor, a second embedding path or a new
memory authority.

## Delivered contracts

- named vector profile;
- payload index profile;
- collection profile;
- point projection envelope;
- model migration plan;
- deterministic inspection report.

## Locked decisions

- SQL remains the authority.
- Qdrant is reconstructible.
- no raw authoritative content enters payloads.
- payload indexes are defined before ingestion.
- one collection per task is forbidden.
- named vectors share a point only when identity and payload are compatible.
- collection alias swap is used for incompatible or independently validated
  migrations.
- no qdrant-client dependency is introduced.
- no Qdrant write is performed.
- ControlProxy is unchanged.

## Verification

The focused tests cover named-vector construction, mandatory payload indexes,
reference-only point payloads, SQL/profile compatibility, raw-content refusal,
named-vector migration, alias migration and deterministic reports.
