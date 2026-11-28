# Qdrant named hybrid-query adapter

```text
DenseQueryEmbedding -----------+
                               |
SparseLexicalQuery ------------+--> LoveQdrantHybridQueryAdapter
                                         |
                                         v
                              existing qdrant-client membrane
                                         |
                         query_points(using=<named vector>)
                                         |
                                         v
                             reference-only candidates
                                         |
                                         v
                                SQL rehydration
```

This unit does not create or migrate the Qdrant collection. The canonical
collection lifecycle remains a separate controlled write boundary.
