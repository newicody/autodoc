# 0244-r1-prod_server_openrc_launcher_surface

Adds a validation-only OpenRC launcher surface for the production server. The
patch includes an example openrc-run service file and validator. It does not
install the service or call OpenRC.

Apply:

```bash
python apply_patch_queue.py --patch 0244-r1-prod_server_openrc_launcher_surface --dry-run --allow-dirty
python apply_patch_queue.py --patch 0244-r1-prod_server_openrc_launcher_surface --commit --push --allow-dirty
```
