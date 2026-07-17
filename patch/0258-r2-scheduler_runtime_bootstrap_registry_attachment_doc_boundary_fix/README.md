# 0258-r2-scheduler_runtime_bootstrap_registry_attachment_doc_boundary_fix

Tiny documentation/rule boundary fix for 0258.

It fixes the exact phrase required by the 0258 rule test and clarifies that the
Scheduler owns Autodoc runtime objects, not PostgreSQL/Qdrant/OpenVINO external
service daemons.

Apply on top of 0258-r1 after the rule failure:

```bash
python apply_patch_queue.py --patch 0258-r2-scheduler_runtime_bootstrap_registry_attachment_doc_boundary_fix --commit --push --allow-dirty
```
