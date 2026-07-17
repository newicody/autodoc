# Changelog — 0287-r7-r15-r3-r3-r2

- remove process discovery from the imported-runtime domain contract;
- require explicit creator and current process identities at lease boundaries;
- inject `os.getpid()` only from the preview tool;
- restore explicit `validate_imported_actions_runtime_ports` reuse;
- retain lease compatibility for legacy direct-port factories;
- retain reverse-order exact-once cleanup and replay receipts;
- add cumulative architecture rules for process-identity injection;
- change no remote-mutation or backend behavior.
