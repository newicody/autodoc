# Phase 0287-r7-r15-r3-r7 — OpenVINO E5 async query adapter

## Result

The installed runtime now has a narrow asynchronous adapter between the
already-built multilingual-e5-small pipeline and `DenseQueryEmbedding`.

The adapter performs no runtime construction. It receives an existing pipeline,
adds the locked `query:` prefix, awaits `embed_text()`, validates the normalized
384-dimensional result and returns the existing dense-query contract.

## Boundaries

- existing E5 pipeline reused;
- no nested event loop;
- no `asyncio.run()` in runtime code;
- no Scheduler construction;
- no Qdrant or PostgreSQL call;
- no raw vector in receipts;
- E5 dimension remains exactly 384.

## Next unit

The next unit is **async hybrid retrieval execution**. It will add an async
variant of the existing retrieval composition, await this adapter, and keep the
Qdrant executor and SQL-authority reads behind their existing injected ports.
## r7-r1 correction

The runtime docstring now states the boundary without spelling the forbidden call.
