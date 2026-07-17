# 0282-r3-projectv2-parent-theme-query-normalization

Extends the existing 0272 query-only ProjectV2 item query and adds the pure
0282-r3 parent/theme normalizer.

```text
Repo autodoc: OUI
Repo projects: NON
existing_query_extended: true
parallel_query_transport_added: false
new_cli_added: false
new_adapter_added: false
projects_repository_change_required: false
```

Apply:

```bash
python apply_patch_queue.py \
  --patch 0282-r3-projectv2-parent-theme-query-normalization \
  --dry-run \
  --allow-dirty
```
