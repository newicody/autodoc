# Phase 0287-r7-r8-r2 — context revision SQL authority report

## Objective

Introduce an executable, versioned SQL authority for semantic context
revisions without changing the historical `missipy.sql_context_store.v1`
record contract.

The phase answers four architecture questions:

1. SQL stores durable identities, content, revision membership, relations,
   artifact metadata and projection provenance.
2. Heavy bytes remain in content-addressed storage such as ZFS.
3. Qdrant stores reconstructible vector projections, not authority.
4. ControlProxy route generations remain transport lifecycle state and do not
   become semantic context revisions.

## Reuse audit

Reused unchanged:

- `SqlContextRecord` and `DbApiSqlContextStore` for historical records;
- `SqlContextStorePolicy` for DB-API parameter style and commit policy;
- existing SQL -> OpenVINO/E5 -> Qdrant paths;
- existing typed references, immutable readback and digest conventions.

A distinct module is justified because the historical store has one record
 table and one `parent_ref`; changing it to a revision DAG would alter its
public meaning. The new module therefore provides an explicit companion
contract and a bridge from `SqlContextRecord`.

## Public schemas

- `missipy.context.authority_object.v1`;
- `missipy.context.artifact_descriptor.v1`;
- `missipy.context.relation.v1`;
- `missipy.context.revision_membership.v1`;
- `missipy.context.revision.v1`;
- `missipy.context.vector_projection_metadata.v1`;
- `missipy.context.revision_bundle.v1`;
- `missipy.context.sql_write_result.v1`.

## SQL organization

The DB-API store owns normalized tables for:

- authority objects and small structured content;
- artifact descriptors pointing to content-addressed storage;
- immutable semantic revisions;
- multiple revision parents;
- complete membership snapshots with active, superseded or invalidated state;
- graph relations and provenance edges;
- vector-projection metadata.

No SQL table stores raw vector values, mmap addresses or MMIO pointers.
Projection metadata records source digest, embedding profile, model revision,
dimension, vector name, collection, point id and state so a projection can be
verified or rebuilt.

## Context graph semantics

A context may form a DAG rather than a strict tree. A revision may have several
parents, enabling branch comparison and explicit merges. Each revision stores
a complete reference snapshot; supersession and invalidation remain visible
instead of deleting historical knowledge.

The user-facing hierarchy is therefore a view over SQL relations and revision
membership, not the physical authority model itself.

## Executable boundary

`DbApiContextRevisionAuthorityStore` supports:

- schema initialization on SQLite tests or an injected PostgreSQL DB-API
  connection;
- immutable insert with exact idempotent replay;
- collision rejection;
- parent and membership reference validation;
- branch and merge lineage;
- revision bundle readback;
- source-digest verification before projection metadata is accepted.

`SQLiteContextRevisionAuthorityStore` is available only as a test and local
preview convenience. No PostgreSQL driver is imported.

## Effects and exclusions

- SQL schema and local DB-API writes: implemented;
- existing production consumer wiring: not changed;
- Qdrant collection or point creation: not performed;
- OpenVINO call: not performed;
- Scheduler change: not performed;
- ControlProxy change: not performed;
- EventBus publication: not performed;
- GitHub mutation: not performed;
- installation change: none.

## Validation

The targeted tests prove:

- legacy v1 SQL records bridge without mutation;
- branch and merge revisions rehydrate deterministically;
- immutable writes replay exactly and reject collisions;
- missing parents or members fail closed;
- projection digests must match SQL authority;
- projection metadata and SQL schema contain no vector values;
- revision references are deterministic.

## Next phase

`0287-r7-r8-r3` will define the canonical Qdrant payload, named-vector profile,
filter fields and payload-index plan. It will consume the SQL authority
metadata introduced here and will not move semantic authority into Qdrant.
