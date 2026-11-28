# Qdrant canonical profile — 0287-r7-r8-r3

## Decision

SQL remains the authority for identities, context revisions, relations, content
digests, artefacts and projection provenance. Qdrant is reconstructible and
contains vectors plus a small reference payload. There is no raw authoritative
content in the Qdrant payload.

This patch adds no qdrant-client dependency and performs no Qdrant write.
ControlProxy is unchanged and remains responsible for route transport, not
knowledge ownership.

## Collection strategy

A bounded collection is selected by compatible point identity and payload
shape. Payload partitioning is used for projects, branches, revisions,
conversations, specialists and laboratories. One collection per task, Issue,
specialist or context revision is forbidden.

Named vectors are used when the same authoritative object and payload need
more than one representation. The initial target is:

- `dense_e5_v1` for the existing 384-dimensional normalized E5 space;
- a later sparse lexical vector for exact identifiers and rare terms;
- a later multivector only after measured late-interaction benchmarks.

The roadmap target for r8-r4 is dense E5 + sparse retrieval, fusion, grouping
and SQL rehydration. This patch only describes the vector spaces.

## Canonical payload

The point payload contains references and filters:

- `sql_ref` and `source_ref`;
- `source_content_digest`;
- `context_revision_ref` and `branch_ref`;
- `project_ref` and `conversation_ref`;
- `artifact_kind` and `contribution_kind`;
- `specialist_ref` and `laboratory_ref`;
- `security_scope`;
- `valid` and `superseded_by`;
- `projection_ref`.

It does not contain source text, file bytes, local paths, model objects or raw
vector values. SQL metadata is used to reconstruct or validate the point.

## Index policy

All fields used for scope filtering receive explicit payload indexes. The
policy requires payload indexes before ingestion so that filtered vector indexes can be
constructed with the expected topology.

`project_ref` is the tenant key and `security_scope` is the principal/scope
key. Branch and context revision filters prevent retrieval from unrelated or
superseded knowledge branches.

## Model migration

Two migration strategies are versioned:

1. **named-vector backfill** when the same collection, point identity and
   payload remain compatible;
2. **collection alias swap** when the payload, scaling boundary, collection
   topology or independent validation requires a separate collection.

Both strategies require re-embedding, background backfill, validation and
operator approval. The source projection is not deleted automatically.

## Boundaries

- SQL remains the authority.
- Qdrant is reconstructible.
- OpenVINO remains the local embedding producer.
- no raw authoritative content is stored in Qdrant payloads;
- no qdrant-client dependency is added;
- no Qdrant write or collection mutation is performed;
- Scheduler and ControlProxy are unchanged;
- hybrid search belongs to r8-r4.
