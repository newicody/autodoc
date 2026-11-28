# Live Qdrant projection probe

```text
preview
  installed INI
      |
      v
  PostgreSQL authority
      |
      +-- object exists
      +-- revision exists
      +-- active membership
      |
      v
  plan_digest

execute (approval + environment + digest)
  PostgreSQL object/revision
      |
      v
  existing OpenVINO E5 pipeline (`passage:`)
      |
      v
  existing r11 live projection
      |
      v
  existing Qdrant executor upsert (one point)
      |
      +--> SQL `VectorProjectionMetadata`
      |
      v
  exact Qdrant retrieve (`with_vectors=False`)
      |
      v
  SQL source/projection rehydration
```

The probe is not an orchestrator. It is a bounded operator tool that composes
already-existing ports and closes the PostgreSQL/Qdrant resources it opens.
