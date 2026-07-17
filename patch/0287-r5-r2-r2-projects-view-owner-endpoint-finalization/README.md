# 0287-r5-r2-r2-projects-view-owner-endpoint-finalization

Run the content-addressed repair from the Autodoc repository first:

```bash
python - <<'PY'
from pathlib import Path

path = Path(
    "templates/github/projects-repository/scripts/"
    "reconcile_projectv2_configuration.py"
)
old = (
    'views_endpoint = '
    'f"users/{plan.user_id}/projectsV2/{plan.number}/views"'
)
new = (
    'views_endpoint = '
    'f"users/{plan.owner}/projectsV2/{plan.number}/views"'
)

source = path.read_text(encoding="utf-8")
count = source.count(old)
if count != 1:
    raise SystemExit(
        f"endpoint repair aborted: expected exactly one old occurrence, got {count}"
    )

path.write_text(source.replace(old, new), encoding="utf-8")
print(f"repaired: {path}")
PY
```

Then apply the documentation/test closure:

```bash
python apply_patch_queue.py \
  --patch 0287-r5-r2-r2-projects-view-owner-endpoint-finalization \
  --commit \
  --push \
  --allow-dirty
```
