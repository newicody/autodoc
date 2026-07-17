# OpenVINO E5 async query adapter

```text
already-built multilingual-e5-small pipeline
                  |
                  | await embed_text("query: ...")
                  v
LoveOpenVinoE5AsyncQueryEmbedder
                  |
                  | DenseQueryEmbedding (384, normalized)
                  v
future async hybrid retrieval execution
```

The adapter is a signature boundary, not a runtime factory. The future
tool-bounded composer remains responsible for constructing the existing E5
pipeline from installed configuration.
The r7-r1 correction changes documentation wording only; the async boundary is unchanged.
