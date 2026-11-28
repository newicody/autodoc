# Changelog — 0287 R7 R15 R2 R2 R3

- made the dynamic CLI test loader compatible with Python 3.14 dataclasses;
- registered source-file modules in `sys.modules` before `exec_module()`;
- restored the prior module entry when execution fails;
- added a rule locking the correct import order;
- changed no production runtime or remote-mutation behavior.
