# GitHub Actions artifact → Copilot publication cycle — 0287 r16-r4-r3

## Goal

Compose the existing read-only artifact scan/fetch and the existing local
ready-run Issue-comment publisher into one bounded operational invocation.

This is the command that an external process authority such as `fcron` may call.
It is not a new scheduler, daemon, worker pool, polling loop, or laboratory
orchestrator.

## Reused surfaces

1. `tools/run_github_actions_artifact_scan_once_live_0272.py`
2. `tools/run_github_actions_ready_run_copilot_issue_publication_once_0287.py`

The first child reads GitHub Actions and synchronizes the durable local raw
dataset. The second child consumes strict `ready_runs`, plans and confirms the
Issue-comment mutation, verifies readback, and records its completion receipt.

## One-shot sequence

```text
external fcron invocation
    -> acquire non-blocking local lock
    -> scan/fetch Actions artifacts once
    -> persist exact scan child report
    -> if scan valid and execute approved:
         publish uncompleted ready-run advisories once
    -> persist exact publication child report
    -> persist combined cycle report
    -> exit
```

An overlapping invocation exits successfully with `status=overlap-skipped`.
It never waits, polls, or starts a resident process.

## Execute gates

Operational execution requires:

- a `policy:` decision identifier;
- `operator-decision=approve`;
- `AUTODOC_REMOTE_MUTATION_ALLOWED=true`;
- `AUTODOC_ISSUE_PUBLICATION_ALLOWED=true`.

GitHub Actions remains `issues: read`. Remote Issue mutation remains local and
controlled.

## Local configuration

The existing private files remain authoritative:

- `.var/config/github_projects_artifact_scan.ini`
- `.var/config/github_artifact_server_fetch.ini`

No `.var` configuration is copied to `newicody/projects`.

A later deployment step may point the existing fcron command at this one-shot
tool. This unit only provides and validates the composable command.
