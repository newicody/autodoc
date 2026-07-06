# 0121 — GitHub Project scenario contract

Adds a reference-only GitHub Project baby-fork scenario packet:

```text
GitHub artifact -> SourceCandidate SQL -> ContextExplorationPlan -> LLMSpecialistResult -> GitHubProjectPublication
```

No GitHub API, HTTP, socket, Qdrant, OpenVINO, PostgreSQL, LLM runtime, Scheduler, Dispatcher, Queue, PolicyEngine, EventBus, or RouteRuntimeManager change is introduced.

Apply:

```bash
python apply_patch_queue.py --patch 0121-github_project_scenario --dry-run
python apply_patch_queue.py --patch 0121-github_project_scenario --commit --push
```
