# 0135 operational note — vector indexing uses existing OpenVINO path

0135 does not add a new runtime or worker.  It proves that the existing vector indexing contract and existing OpenVINO/E5 embedding membrane can exchange data.

```text
Scheduler
-> VectorIndexingJobPlan
-> VectorEmbeddingJob
-> OpenVINOEmbeddingText
-> existing OpenVINO/E5 adapter membrane
-> vector validation
-> Qdrant projection later
```

The RouteProxy and `/dev/shm` route work remains separate.  This patch prepares the embedding side without touching Scheduler.run().
