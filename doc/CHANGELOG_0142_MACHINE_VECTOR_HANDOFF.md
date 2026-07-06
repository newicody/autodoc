# Changelog 0142 — machine vector handoff

Changed:

- `tools/run_local_vector_indexing_live_smoke.py`
  - generates `.var/smoke/e5_vector_0142.json` through `tools/embed_e5.py --format json --full-vector`
  - passes the file to the Qdrant smoke tool with `--vector-json`
  - supports strict vector handoff without parsing human previews

- `tools/run_qdrant_projection_live_smoke.py`
  - accepts `--vector-json`
  - validates the machine vector dimension
  - uses the supplied vector for Qdrant upsert/search

Added tests/docs/rules for 0142.

Not changed:

- no Scheduler change
- no RouteProxy change
- no OpenVINO adapter fork
- no Qdrant adapter fork
- no daemon
