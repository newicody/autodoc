# Context revision SQL authority — 0287-r7-r8-r2

## Responsibility split

```text
SQL
= identities, revisions, relations, membership, artifacts and provenance

ZFS / content-addressed storage
= heavy bytes

Qdrant
= reconstructible vector projections and recall

OpenVINO
= local embedding and inference production

Scheduler
= task execution and context-impact decisions

ControlProxy
= authorized transport and route-generation lifecycle only
```

## Authority model

```text
context:study
├── context-revision:r1
│   ├── sql:source:a                 active
│   └── artifact:model-3d            active
├── context-revision:r2a             parent r1
│   ├── sql:source:a                 superseded by sql:source:b
│   ├── sql:source:b                 active
│   └── artifact:model-3d            active
├── context-revision:r2b             parent r1
│   ├── sql:source:a                 active
│   └── artifact:model-3d            active
└── context-revision:r3              parents r2a + r2b
    ├── sql:source:b                 active
    └── artifact:model-3d            active
```

This is a revision DAG. A hierarchical workbook can be rendered from it, but
SQL does not force all knowledge into one directory tree.

## Projection metadata

SQL records only the metadata needed to verify and rebuild a Qdrant point:

```text
source_ref
source_content_digest
embedding_profile_ref
model_ref
model_revision
dimension
normalized
vector_name
collection_name
point_id
projection_state
```

Raw vectors are not stored in these SQL tables. Qdrant remains disposable and
reconstructible from SQL/ZFS authority plus the declared model bundle.

## Compatibility

`missipy.sql_context_store.v1` remains unchanged. The bridge
`build_authority_object_from_sql_context_record()` imports one historical
record into the new authority without changing its original identity or store.
