# Roadmap B Aider Orchestrator

The Roadmap B orchestrator is a Python script that uses Aider to produce patch
bundles, then applies them through the existing patch queue.

Aider is only used as a patch-bundle author. It should not be treated as the
source of truth and should not directly mutate the final development path.

## Plan-only run

```bash
python tools/roadmap_b_aider_orchestrator.py   --no-aider   --max-steps 1   --max-minutes 180
```

## One automated step

```bash
python tools/roadmap_b_aider_orchestrator.py   --max-steps 1   --max-minutes 180   --archive-patch-bundles
```

## With a specific Aider model

```bash
python tools/roadmap_b_aider_orchestrator.py   --max-steps 1   --aider-extra-arg --model   --aider-extra-arg openai/gpt-5.5
```

## Validation gates

The orchestrator requests operator validation if the patch touches:

```text
tests/rules/
doc/code-rules/
dependency files
Scheduler/runtime paths
large retroactive diffs
```

## Generated reports

```text
doc/maintenance/roadmap_b_aider_prompt.md
doc/maintenance/roadmap_b_aider_orchestrator_run_report.json
```

These generated files are operator artifacts. Version them only when the operator
wants to preserve the run.
