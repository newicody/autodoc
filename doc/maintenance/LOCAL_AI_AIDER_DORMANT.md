# Local AI / Aider Dormant Mode

Aider is dormant.

It is not deleted because the experiment is useful context, but it is not part of the active development path.

## Active development path

```text
ChatGPT Plus 5.5 Advanced
→ patch bundle
→ apply_patch_queue.py
→ tests
→ commit/push
```

## Dormant path

```text
Aider/API
→ paused
```

Aider can be revisited later only after:

```text
- context capsules are much smaller
- generated files are outside versioned documentation paths
- interactive mode is explicit
- model/API cost and rate limits are understood
```

## Cleanup artifacts

The failed Aider experiment generated local/operator files:

```text
doc/maintenance/roadmap_b_aider_prompt.md
doc/maintenance/roadmap_b_aider_orchestrator_run_report.json
patch/0039-part8_roadmap_b_part8_1_local_data_contract/
```

These files are not source-of-truth design documents. They are generated
operator artifacts and can be removed.

## Rule

A local model, Aider, or any other coding helper must not become the authority.
The repository, contracts, tests, rules, and patch queue remain the authority.
