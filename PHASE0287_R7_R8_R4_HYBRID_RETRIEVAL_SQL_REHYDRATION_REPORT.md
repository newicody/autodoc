# Phase 0287-r7-r8-r4 — hybrid retrieval and SQL rehydration report

## Objective

Close the read side of the semantic context path without creating a parallel
search engine:

```text
task query
→ OpenVINO/E5 query embedding through the existing injected boundary
→ dense named-vector search in Qdrant
→ sparse lexical named-vector search in Qdrant
→ identical authority/context/security filters
→ reciprocal-rank fusion
→ grouping by document, contribution or source
→ SQL reference selection
→ SQL-authoritative rehydration
```

## Reuse audit

Reused surfaces:

- `context_revision_sql_authority_0287.py` for revisions, active memberships,
  context objects and artifact descriptors;
- `qdrant_canonical_profile_0287.py` for shared point identity, named vectors,
  reference-only payloads and canonical filter fields;
- the existing OpenVINO/E5 query embedding boundary through an injected port;
- the existing Qdrant projection/executor family through an injected hybrid
  query extension.

No second Qdrant client, SQL store, Scheduler, EventBus, ControlProxy or model
runtime is introduced.

## Added contracts

- `missipy.retrieval.hybrid_filter.v1`
- `missipy.retrieval.dense_query_embedding.v1`
- `missipy.retrieval.sparse_lexical_query.v1`
- `missipy.retrieval.hybrid_query.v1`
- `missipy.retrieval.hybrid_candidate.v1`
- `missipy.retrieval.hybrid_hit.v1`
- `missipy.retrieval.rehydrated_authority_item.v1`
- `missipy.retrieval.hybrid_result.v1`
- `missipy.retrieval.hybrid_report.v1`

## Safety and authority

Every dense and sparse candidate must match:

- SQL authority reference when configured;
- context revision;
- branch;
- project;
- security scope;
- optional conversation, specialist and laboratory scopes;
- validity and non-superseded policy;
- optional artifact/contribution kinds.

The Qdrant hit only selects a typed SQL reference.  The selected reference must
be active in the requested SQL revision and its Qdrant source digest must match
the SQL content digest before content is returned.

## Fusion and diversity

Dense and sparse ranks are fused with reciprocal-rank fusion.  The final list
can be grouped by:

- `document_ref`;
- `contribution_ref`;
- `source_ref`;
- no grouping.

Grouping happens after fusion, so a source supported by both retrieval paths is
preferred without allowing many chunks of the same document to occupy the
whole result budget.

## Boundaries

- SQL remains durable authority.
- Qdrant remains a reconstructible projection and reference recall surface.
- OpenVINO/E5 remains behind the existing injected embedding boundary.
- No Qdrant write, collection creation or index mutation is performed.
- No raw dense vector is serialized in result/report mappings.
- No ControlProxy, Scheduler, EventBus, GitHub or laboratory runtime is changed.
- `INSTALLATION.md` is unchanged because no deployment surface changes.

## Validation

Targeted tests cover:

- deterministic sparse lexical encoding;
- complete authority/context/security filters;
- distinct dense and sparse named vectors;
- RRF fusion and document grouping;
- end-to-end SQL rehydration;
- branch/scope rejection;
- digest mismatch rejection;
- inactive revision membership rejection;
- missing sparse vector rejection;
- result/report authority boundaries.

## Next unit

`0287-r7-r8-r5` will add semantic context-revision impact contracts and the
Scheduler-owned decisions `snapshot`, `checkpoint_rebase`, `restart`, `fork`
and `notify_only`.  It will consume retrieval and SQL references but will not
make the EventBus or ControlProxy authoritative.
