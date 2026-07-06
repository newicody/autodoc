# 0107-controlproxy_graph_root_alignment

Architecture graph root alignment after 0101-0106.

This patch adds a root-attached runtime overlay and rule tests. It does not add runtime code, CLI, daemon, watcher, new bus or Scheduler/Dispatcher/Policy/Queue changes.

Apply with:

```bash
python apply_patch_queue.py --patch 0107-controlproxy_graph_root_alignment --dry-run
python apply_patch_queue.py --patch 0107-controlproxy_graph_root_alignment --commit --push
```
