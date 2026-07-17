# 0287-r7-r15-r3-r15-tool-bounded-installed-runtime-composer

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r15-tool-bounded-installed-runtime-composer \
  --dry-run \
  --allow-dirty
```

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r15-tool-bounded-installed-runtime-composer \
  --commit \
  --push \
  --allow-dirty
```

## Installed configuration after integration

In `.var/config/love_installed_runtime.ini`:

```ini
[provider]
factory = context.love_tool_bounded_installed_runtime_composer_0287:build_tool_bounded_installed_runtime

[scheduler]
lifecycle = tool-bounded
```

Do not run the imported Actions loop yet. The next unit switches its smoke call
from the deterministic entry point to the r14 live entry point.
