# 0287-r7-r8-r3 — Qdrant canonical profile

- add immutable named-vector, payload-index and collection profiles;
- bridge the existing E5 embedding-space profile into a named vector;
- bridge r8-r2 SQL vector metadata into a reference-only Qdrant point;
- require branch, revision, project, conversation and security filters;
- forbid raw content, vectors and local paths in Qdrant payloads;
- forbid one collection per task;
- define named-vector backfill and collection-alias migration plans;
- add no qdrant-client dependency and perform no remote mutation.
