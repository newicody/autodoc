# 0249-r1-prod_server_eventbus_attributes_readiness

Adds EventBus advanced attribute readiness for required envelope fields,
reference attributes, redacted fields, and refs-only payload policy. This phase
does not create EventBus or publish events.

Apply:

```bash
python apply_patch_queue.py --patch 0249-r1-prod_server_eventbus_attributes_readiness --dry-run --allow-dirty
python apply_patch_queue.py --patch 0249-r1-prod_server_eventbus_attributes_readiness --commit --push --allow-dirty
```
