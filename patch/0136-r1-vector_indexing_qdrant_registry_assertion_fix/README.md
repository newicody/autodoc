# 0136-r1 — Vector indexing Qdrant registry assertion fix

Fixes one overly strict 0136 integration assertion.

0136 originally required literal collection names:

- `contracts_e5_384`
- `specialist_outputs_e5_384`

The complete repository registry can expose collection roles without those exact strings. 0136-r1 keeps the architectural intent — reuse the existing `VectorCollectionRegistry` and existing Qdrant projection adapter — while avoiding a brittle literal-name check.

Apply after failed/applied 0136 with a dirty working tree:

```bash
python apply_patch_queue.py \
  --patch 0136-r1-vector_indexing_qdrant_registry_assertion_fix \
  --commit \
  --push \
  --allow-dirty
```
