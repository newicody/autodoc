# Hybrid retrieval with SQL rehydration

## Runtime composition

```text
SpecialistTaskRequest
  │ query text + active revision/branch/security refs
  ▼
DenseQueryEmbedder port
  │ existing OpenVINO/E5 query vector, role=query
  ├───────────────────────────┐
  ▼                           ▼
Qdrant dense search       Sparse lexical encoder
  │ dense_e5_v1               │ sparse_lexical_v1
  └──────────────┬────────────┘
                 ▼
        common filtered candidates
                 ▼
       reciprocal-rank fusion
                 ▼
 document/contribution/source grouping
                 ▼
       typed SQL authority refs
                 ▼
 active revision + digest verification
                 ▼
        SQL authoritative content
```

## Filter rule

Dense and sparse paths receive the same mandatory filter.  A candidate is
rejected locally if its payload does not match the requested revision, branch,
project, security scope or optional SQL authority/conversation/specialist/
laboratory scopes.

## Data placement

```text
SQL
  authority objects, artifact descriptors, revisions, memberships, digests

Qdrant
  named vectors, reference payloads, filter fields and scores

OpenVINO/E5
  query embedding only behind the existing adapter

retrieval result
  fused references plus content rehydrated from SQL
```

Qdrant payloads must not contain authoritative body text, heavy bytes, local
paths or vectors.  The serialized dense embedding description includes model,
revision, dimension and backend, but not vector values.

## Extension points

The injected Qdrant executor can later map this contract to the official Query
API with dense and sparse prefetches, RRF and native grouping.  Local fusion is
kept deterministic so the same behavior can be tested without network access.
Optional reranking remains a later bounded stage after candidate fusion.
