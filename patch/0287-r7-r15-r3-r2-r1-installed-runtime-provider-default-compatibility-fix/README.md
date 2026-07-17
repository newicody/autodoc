# 0287-r7-r15-r3-r2-r1 — installed runtime provider default compatibility fix

## Purpose

Repair the rules-suite incompatibility introduced when r15-r3-r2 replaced the
historical blank `[provider] factory =` example marker with the canonical
provider path.

## Resolution

- restore a literal blank `factory =` in
  `config/love_installed_runtime.example.ini`;
- document the canonical provider path beside the blank setting;
- make `love_installed_runtime_factory_0287` select that canonical provider
  whenever the configured value is empty;
- preserve explicit non-empty compatible provider overrides;
- add focused context and architecture-rule regressions.

The default is not a fake or dummy fallback. It selects the real manual
installed-runtime provider introduced by r15-r3-r2. No Scheduler, SQL, Qdrant or
OpenVINO backend is constructed by this compatibility patch.

## Apply

The failed r15-r3-r2 patch is already present in the working tree. Do not reset
it before applying this correction.

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r2-r1-installed-runtime-provider-default-compatibility-fix \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r2-r1-installed-runtime-provider-default-compatibility-fix \
  --commit \
  --push \
  --allow-dirty
```

## Validation performed

- `git apply --check`: passed;
- `git diff --check`: passed;
- focused behavioral and rule tests: 2 passed;
- historical/current marker compatibility assertions: passed;
- targeted `compileall`: passed;
- Graphviz DOT parse: passed.

The full repository rules and global suite are intentionally delegated to
`apply_patch_queue.py` on the real checkout.
