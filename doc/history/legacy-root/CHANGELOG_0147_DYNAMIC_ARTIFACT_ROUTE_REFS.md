# Changelog 0147 — Dynamic artifact route refs

Added:

- `src/context/artifact_route_refs.py`
- dynamic command/request/result refs derived from `artifact_ref` and `vector_indexing_job_ref`
- CLI flags on `tools/run_scheduler_vector_indexing_smoke.py` for request/result refs and namespaces
- propagation of dynamic refs from the local artifact runner into the existing Scheduler vector smoke tool
- tests, docs, rule addendum, DOT graph, manifest, and test report

0147 removes static 0143/0144 route refs from the artifact runner path without modifying `Scheduler.run()`.
