# Roadmap B Lock

Roadmap B is the active development direction.

The goal is to build a robust local-first foundation before opening real
external integrations.

## Source of truth

```text
local repository / local server = source of truth
GitHub / external systems = review and synchronization surfaces
```

GitHub is not the source of truth.

## Priority order

```text
1. local data contract
2. local document model
3. incremental file scan
4. context bundle builder
5. retrieval evaluation set
6. operator feedback loop
7. only then: real read-only external integration
```

## Closed boundaries

```text
external service calls: closed by default
remote mutation: closed by default
Scheduler execution: closed by default
new dependencies: operator approval required
rules changes: operator approval required
large retroactive refactors: operator approval required
```

## Development method

Every automated step must produce a patch bundle:

```text
patch/<patch-id>/
  README.md
  metadata.json
  patch.diff
```

The patch is then applied through:

```bash
python apply_patch_queue.py --patch <patch-id> --dry-run
python apply_patch_queue.py --patch <patch-id> --commit --push
```

Tests run after each applied step.
