# 0112-r2-route_bridge_boundary_graph_phrase_fix

Fixes the 0112 rule-test graph phrase by adding the exact expected root-attached edge phrase to the DOT file.

Apply on the dirty state left by the failed 0112 run:

```bash
python apply_patch_queue.py --patch 0112-r2-route_bridge_boundary_graph_phrase_fix --allow-dirty --dry-run
python apply_patch_queue.py --patch 0112-r2-route_bridge_boundary_graph_phrase_fix --allow-dirty --commit --push
```
