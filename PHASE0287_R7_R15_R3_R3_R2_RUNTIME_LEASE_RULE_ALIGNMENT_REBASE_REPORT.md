# Phase 0287-r7-r15-r3-r3-r2 — runtime lease rule alignment

## Failure reproduced

The first r15-r3-r3 application compiled and its focused lease tests were
present, but the cumulative rule suite stopped on two regressions:

1. the domain runtime contract imported `os` to obtain the current PID;
2. the preview tool no longer contained the explicit historical call to
   `validate_imported_actions_runtime_ports`.

## Correction

Process identity is now an injected value:

```text
tool / composition
  os.getpid()
      |
      v
runtime lease contract
  current_process_id: int
```

The contract validates only positive integer identities and compares the
injected current identity with the immutable creator identity. It performs no
environment, process, network or transport lookup.

The preview tool again performs the cumulative sequence:

```text
runtime factory
→ acquire lease with current_process_id
→ validate_imported_actions_runtime_ports(lease.ports)
→ r14 on the existing Scheduler
→ Scheduler shutdown
→ lease close with current_process_id
```

Legacy factories returning direct ports remain supported. They are wrapped in a
lease whose creator identity is supplied by the tool. Modern factories must
construct leases with an explicit creator identity.

## Boundaries

- no old rule or historical test is weakened;
- no Scheduler, manager, laboratory or backend is added;
- no PostgreSQL, Qdrant, OpenVINO or GitHub operation is performed;
- E5 remains fixed at 384 dimensions;
- the existing r15-r3-r3 ownership and exact-once cleanup model is preserved.
