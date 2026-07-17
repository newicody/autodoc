# 0272-r8 — ProjectV2 SourceCandidate durable consumer

This patch closes the r7 -> SQL transition without opening OpenVINO/E5,
Qdrant, GitHub mutation, Scheduler or SHM effects.

It adds:

- strict validation of approved `promote`/`merge` r7 gate records;
- deterministic `github_artifact` SQL records using the existing builder;
- insert-if-absent semantics, immutable-collision refusal and idempotent replay;
- mandatory SQL readback;
- an operator CLI reusing the 0260 `DbApiSqlContextStore` discovery/binding;
- architecture, manifest, release, test report and focused tests;
- explicit next steps for `EmbeddingSpaceProfile` and laboratory reuse audit.

Apply from `/home/eric/projet/git/autodoc`:

```bash
unzip -o /mnt/data/0272-r8-github_project_v2_source_candidate_durable_consumer.zip
python apply_patch_queue.py \
  --patch 0272-r8-github_project_v2_source_candidate_durable_consumer \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0272-r8-github_project_v2_source_candidate_durable_consumer \
  --commit \
  --push \
  --allow-dirty
```

Recommended validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_source_candidate_durable_consumer_0272.py \
  tests/tools/test_consume_github_project_v2_source_candidate_gate_0272.py
```

Example execution after producing a promoted/merged r7 gate record:

```bash
PYTHONPATH=src:. python \
  tools/consume_github_project_v2_source_candidate_gate_0272.py \
  --gate-record .var/github/project_v2/decisions/<gate-record>.json \
  --db-path .var/local/sql_context_store.sqlite3 \
  --execute \
  --policy-decision-id policy:0272:r8:durable-consume \
  --format summary
```

No non-stdlib dependency is added. The full repository suite must be run on the
target checkout at `c8ec121` because the build environment used to generate this
bundle could not clone GitHub directly.
