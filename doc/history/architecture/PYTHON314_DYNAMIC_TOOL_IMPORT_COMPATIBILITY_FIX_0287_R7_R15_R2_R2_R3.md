# Python 3.14 dynamic tool import compatibility

The tests load tool scripts under synthetic module names so each scenario gets
an isolated module object.  A source-file import must nevertheless preserve the
normal import invariant that the module is visible in `sys.modules` while its
body executes.

```text
spec_from_file_location
→ module_from_spec
→ sys.modules[name] = module
→ exec_module(module)
→ usable dataclasses and postponed annotations
```

If execution fails, the helper restores the entry that existed before the
attempt, or removes the synthetic entry when none existed.

No production module is made responsible for repairing a non-standard loader.
