# 0287-r7-r15-r3-r2 — manual runtime configuration and provider binding

This patch adds the canonical local configuration and read-only readiness path
for the installed PostgreSQL, Qdrant and OpenVINO runtime.

## Main effects

- preselects the canonical provider in `config/love_installed_runtime.example.ini`;
- configures PostgreSQL `autodoc`, Qdrant alias `autodoc_context_current`, and
  multilingual E5 small on CPU with dimension 384;
- keeps PostgreSQL and Qdrant secrets in environment variables only;
- adds `tools/check_love_installed_runtime_0287.py`;
- adds a provider registry that only returns already-composed live ports;
- does not construct a Scheduler, SQL authority, OpenVINO executor, Qdrant
  client, laboratory, or parallel manager.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r2-manual-runtime-configuration-and-provider-binding \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r2-manual-runtime-configuration-and-provider-binding \
  --commit \
  --push \
  --allow-dirty
```

## Local configuration

After application, merge or copy the example into:

```text
.var/config/love_installed_runtime.ini
```

Keep the existing local PostgreSQL password outside Git:

```bash
export AUTODOC_POSTGRES_PASSWORD='...'
```

Run the read-only readiness check:

```bash
/home/eric/python/bin/python tools/check_love_installed_runtime_0287.py \
  --config .var/config/love_installed_runtime.ini \
  --format json
```

Expected summary:

```text
manual_runtime_valid=True issues=0 postgresql=True qdrant=True openvino=True write_performed=False
```

## Validation performed by the patch builder

- `git diff --check`: passed;
- `git apply --check` on the reconstructed r15-r3-r1 base: passed;
- Python compilation: passed;
- 5 focused configuration/readiness/rule tests: passed;
- Graphviz DOT parsing: passed;
- no `.pyc`, SVG, secret value, or binary patch payload included.

The full repository rule and global suites are intentionally delegated to
`apply_patch_queue.py` on the real checkout.
