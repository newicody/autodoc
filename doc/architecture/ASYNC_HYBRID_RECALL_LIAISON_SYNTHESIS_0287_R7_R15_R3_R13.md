# Async hybrid recall and liaison synthesis

```text
r12 binding
  ├── SQL analysis object A ── Qdrant projection A
  └── SQL analysis object B ── Qdrant projection B
                    |
                    v
         E5 query: embedding (awaited)
                    |
          dense + sparse Qdrant search
                    |
             reciprocal-rank fusion
                    |
       SQL rehydration of A and B required
                    |
        shared mutualization/finalizer
                    |
          final synthesis object + revision
```

No projection is performed in this unit. Qdrant remains a reference-only recall
surface and SQL remains the content authority.
