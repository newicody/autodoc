# 0240-r2-prod_server_initial_config_requirements

Defines the initial production server configuration requirements for Autodoc.
This phase also includes the GitHub artifact-exchange surface already developed:
GITHUB_TOKEN, repository allowlist, ProjectPushFrame import requirement, Copilot
advisory-only policy, and reviewed publication disabled by default.

Use this r2 patch instead of the previous 0240-r1 archive.

Apply:

```bash
python apply_patch_queue.py --patch 0240-r2-prod_server_initial_config_requirements --dry-run --allow-dirty
python apply_patch_queue.py --patch 0240-r2-prod_server_initial_config_requirements --commit --push --allow-dirty
```
