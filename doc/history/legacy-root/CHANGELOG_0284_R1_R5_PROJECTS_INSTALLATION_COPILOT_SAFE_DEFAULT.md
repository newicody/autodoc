# Changelog 0284-r1-r5 — Projects installation Copilot safe default

- Changes the cumulative `newicody/projects` installation default from
  enabled Copilot advisory to disabled.
- Documents explicit post-validation activation.
- Locks use of ephemeral `GITHUB_TOKEN` and rejects a durable
  `AUTODOC_COPILOT_TOKEN` installation instruction.
- Records that an unavailable advisory does not block the authoritative
  request and manifest path.
- Changes no workflow, Scheduler, SQL, Qdrant, OpenVINO or EventBus code.
