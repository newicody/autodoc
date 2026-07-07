# 0160 — Query recall rehydrate contract

Adds one operator-only smoke tool:

```text
tools/run_query_recall_rehydrate_contract_smoke.py
```

It normalizes a user query to E5 `query:` text, accepts a Qdrant-style recall
payload carrying `sql_ref`, and delegates durable rehydrate to 0159.

Apply:

```bash
tar -xJf autodoc_patch_0160-query_recall_rehydrate_contract.tar.xz
python apply_patch_queue.py --patch 0160-query_recall_rehydrate_contract --dry-run --allow-dirty
python apply_patch_queue.py --patch 0160-query_recall_rehydrate_contract --commit --push --allow-dirty
```
